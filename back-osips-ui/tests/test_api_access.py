"""Проверка прав доступа к разделам API по ролям."""

from unittest.mock import AsyncMock, patch


def test_health_is_public(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_endpoints_require_token(client, server_id):
    assert client.get("/api/servers").status_code == 401
    assert client.get(f"/api/servers/{server_id}/dialplan").status_code == 401


def test_wrong_password(client):
    assert client.post("/api/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401


def test_me_returns_permissions(client, qa_headers):
    payload = client.get("/api/auth/me", headers=qa_headers).json()
    assert payload["role"] == "qa"
    assert "dispatcher:read" in payload["permissions"]
    assert "dispatcher:write" not in payload["permissions"]


def test_reader_sees_only_sip_regs(client, reader_headers, server_id):
    page = {"source": "db", "items": [], "total": 0, "users": 0, "page": 1, "per_page": 25, "now_ts": 0}
    with patch("app.api.sipregs.sipregs.list_contacts", new=AsyncMock(return_value=page)):
        assert client.get(f"/api/servers/{server_id}/sip-regs", headers=reader_headers).status_code == 200
    assert client.get(f"/api/servers/{server_id}/dispatcher", headers=reader_headers).status_code == 403
    assert client.get("/api/users", headers=reader_headers).status_code == 403


def test_qa_reads_dispatcher_but_cannot_change_it(client, qa_headers, server_id):
    with patch("app.api.dispatcher.ds.list_destinations", new=AsyncMock(return_value={"rows": [], "mi_available": True, "mi_error": None})):
        assert client.get(f"/api/servers/{server_id}/dispatcher", headers=qa_headers).status_code == 200
    assert client.post(f"/api/servers/{server_id}/dispatcher/reload", headers=qa_headers).status_code == 403
    assert client.post(f"/api/servers/{server_id}/dispatcher/1/state", headers=qa_headers, json={"state": "inactive"}).status_code == 403


def test_admin_can_toggle_node_state(client, admin_headers, server_id):
    row = {"id": 1, "setid": 200, "destination": "sip:10.0.0.1:5060"}
    with (
        patch("app.api.dispatcher.ds.get", new=AsyncMock(return_value=row)),
        patch("app.api.dispatcher.ds.set_state", new=AsyncMock(return_value="OK")) as set_state,
    ):
        response = client.post(f"/api/servers/{server_id}/dispatcher/1/state", headers=admin_headers, json={"state": "inactive"})
    assert response.status_code == 200
    set_state.assert_awaited_once()
    assert set_state.await_args.args[1:] == (200, "sip:10.0.0.1:5060", "inactive")


def test_admin_can_toggle_lb_status(client, admin_headers, server_id):
    with (
        patch("app.api.loadbalancer.lb.get", new=AsyncMock(return_value={"id": 3, "dst_uri": "sip:10.0.0.9"})),
        patch("app.api.loadbalancer.lb.set_status", new=AsyncMock(return_value="OK")) as set_status,
    ):
        response = client.post(f"/api/servers/{server_id}/loadbalancer/3/status", headers=admin_headers, json={"enabled": False})
    assert response.status_code == 200
    assert set_status.await_args.args[1:] == (3, False)


def test_admin_cannot_downgrade_self(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    response = client.put(f"/api/users/{me['id']}", headers=admin_headers, json={"role": "reader"})
    assert response.status_code == 400


def test_new_sections_are_closed_for_reader(client, reader_headers, server_id):
    for path in ("dialplan", "rtpengine", "blacklist/user", "blacklist/global", "address"):
        assert client.get(f"/api/servers/{server_id}/{path}", headers=reader_headers).status_code == 403, path


def test_admin_reads_dialplan_and_reloads(client, admin_headers, server_id):
    page = {"items": [], "total": 0, "page": 1, "per_page": 25}
    with patch("app.api.dialplan.dp.list_rules", new=AsyncMock(return_value=page)):
        assert client.get(f"/api/servers/{server_id}/dialplan", headers=admin_headers).status_code == 200

    with patch("app.api.dialplan.dp.reload", new=AsyncMock(return_value="OK")) as reload:
        assert client.post(f"/api/servers/{server_id}/dialplan/reload", headers=admin_headers).status_code == 200
    # без указания партиции opensips перечитывает все
    assert reload.await_args.args[1:] == (None,)


def test_dialplan_rejects_unknown_match_op(client, admin_headers, server_id):
    payload = {"dpid": 1, "match_exp": "1234", "match_op": 5}
    assert client.post(f"/api/servers/{server_id}/dialplan", headers=admin_headers, json=payload).status_code == 422


def test_admin_toggles_rtpengine_socket(client, admin_headers, server_id):
    row = {"id": 2, "socket": "udp:10.0.0.9:2223", "set_id": 0}
    with (
        patch("app.api.rtpengine.rtpe.get", new=AsyncMock(return_value=row)),
        patch("app.api.rtpengine.rtpe.set_enabled", new=AsyncMock(return_value="OK")) as set_enabled,
    ):
        response = client.post(f"/api/servers/{server_id}/rtpengine/2/enabled", headers=admin_headers, json={"enabled": False})
    assert response.status_code == 200
    assert set_enabled.await_args.args[1:] == (0, "udp:10.0.0.9:2223", False)


def test_blacklist_kinds_use_their_own_tables(client, admin_headers, server_id):
    page = {"kind": "user", "table": "userblacklist", "needs_reload": False, "items": [], "total": 0, "page": 1, "per_page": 25}
    with patch("app.api.blacklist.bl.list_entries", new=AsyncMock(return_value=page)) as list_entries:
        assert client.get(f"/api/servers/{server_id}/blacklist/user", headers=admin_headers).status_code == 200
    assert list_entries.await_args.args[1] == "user"

    with patch("app.api.blacklist.bl.list_entries", new=AsyncMock(return_value=page | {"kind": "global"})) as list_entries:
        assert client.get(f"/api/servers/{server_id}/blacklist/global", headers=admin_headers).status_code == 200
    assert list_entries.await_args.args[1] == "global"


def test_blacklist_only_filter_is_validated(client, admin_headers, server_id):
    url = f"/api/servers/{server_id}/blacklist/user"
    assert client.get(url, headers=admin_headers, params={"only": "grey"}).status_code == 422


def test_address_write_requires_permission(client, qa_headers, admin_headers, server_id):
    payload = {"grp": 1, "ip": "10.0.0.1", "mask": 32}
    assert client.post(f"/api/servers/{server_id}/address", headers=qa_headers, json=payload).status_code == 403

    with patch("app.api.address.addr.create", new=AsyncMock(return_value=11)):
        response = client.post(f"/api/servers/{server_id}/address", headers=admin_headers, json=payload)
    assert response.status_code == 201 and response.json()["id"] == 11
