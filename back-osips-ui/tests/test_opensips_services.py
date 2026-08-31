from app.services.dispatcher import normalize_uri
from app.services.loadbalancer import _state_from_mi


def test_normalize_uri_adds_scheme_and_lowercases():
    assert normalize_uri("10.0.0.1:5060") == "sip:10.0.0.1:5060"
    assert normalize_uri(" SIP:10.0.0.1 ") == "sip:10.0.0.1"
    assert normalize_uri(None) == ""


def test_lb_state_mapping():
    assert _state_from_mi({"enabled": "yes", "auto-reenable": "on"}) == "active"
    # выключен вручную через lb_status - auto-reenable снимается
    assert _state_from_mi({"enabled": "no", "auto-reenable": "off"}) == "inactive"
    # выключен пробингом - auto-reenable остаётся
    assert _state_from_mi({"enabled": "no", "auto-reenable": "on"}) == "probing"


# --------------------------------------------------------------------------------------
# sip-регистрации (таблица location)
# --------------------------------------------------------------------------------------


def test_sipregs_status_by_expires():
    from app.services import sipregs

    now = 1_700_000_000
    assert sipregs._status(0, now) == "permanent"  # постоянный контакт
    assert sipregs._status(10, now) == "expired"  # UL_EXPIRED_TIME
    assert sipregs._status(now - 5, now) == "expired"
    assert sipregs._status(now + 60, now) == "active"


def test_sipregs_normalize_row():
    from app.services import sipregs

    now = 1_700_000_000
    row = {
        "contact_id": 7,
        "username": "1234201",
        "domain": "voip.local",
        "contact": "sip:1234201@10.0.0.5:5060",
        "received": "sip:10.0.0.5:5060",
        "expires": now + 120,
        "expires_at": "2023-11-14 22:22:00",
        "q": 1.0,
        "user_agent": "Polycom",
    }
    item = sipregs._normalize(row, now)
    assert item["id"] == 7
    assert item["aor"] == "1234201@voip.local"
    assert item["status"] == "active"
    assert item["expires_in"] == 120

    permanent = sipregs._normalize(row | {"expires": 0}, now)
    assert permanent["status"] == "permanent"
    assert permanent["expires_at"] is None and permanent["expires_in"] is None


def test_sipregs_flatten_ul_dump():
    from app.services import sipregs

    now = 1_700_000_000
    dump = {
        "Domains": [
            {
                "name": "location",
                "hash_size": 512,
                "AORs": [
                    {
                        "AOR": "1234201@voip.local",
                        "Contacts": [
                            {
                                "Contact": "sip:1234201@10.30.1.21:5060",
                                "ContactID": "1",
                                "Expires": 1780,
                                "Q": "1.00",
                                "Callid": "a1b2c3",
                                "Cseq": 14,
                                "User-agent": "Polycom",
                                "Received": "sip:10.30.1.21:5060",
                                "State": "CS_SYNC",
                                "Flags": 0,
                                "Cflags": "",
                                "Socket": "udp:10.10.10.11:5060",
                                "Methods": 8063,
                            }
                        ],
                    },
                    {"AOR": "1234301@voip.local", "Contacts": [{"Contact": "sip:gw", "ContactID": "4", "Expires": "permanent"}]},
                    {"AOR": "1234202@voip.local", "Contacts": [{"Contact": "sip:old", "ContactID": "3", "Expires": "expired"}]},
                ],
            }
        ]
    }

    rows = sipregs.flatten_dump(dump, now)
    assert len(rows) == 3

    active = next(row for row in rows if row["id"] == 1)
    assert active["username"] == "1234201" and active["domain"] == "voip.local"
    assert active["status"] == "active" and active["expires_in"] == 1780
    assert active["state"] == "CS_SYNC" and active["table"] == "location"
    assert active["q"] == 1.0 and active["cseq"] == 14

    assert next(row for row in rows if row["id"] == 4)["status"] == "permanent"
    assert next(row for row in rows if row["id"] == 3)["status"] == "expired"

    # deleted (UL_EXPIRED_TIME) тоже показываем как истёкшую
    deleted = sipregs._normalize_dump("777@d", {"ContactID": "9", "Expires": "deleted"}, "location", now)
    assert deleted["status"] == "expired"

    assert sipregs.flatten_dump({}, now) == []


def test_sipregs_dump_aor_without_domain():
    from app.services import sipregs

    # при use_domain=0 в AOR только номер
    row = sipregs._normalize_dump("1234201", {"ContactID": "1", "Expires": 60}, "location", 0)
    assert row["username"] == "1234201" and row["domain"] == ""


# --------------------------------------------------------------------------------------
# rtpengine
# --------------------------------------------------------------------------------------


def test_rtpengine_state_mapping():
    from app.services import rtpengine

    assert rtpengine._state(0, 0) == "active"
    # выключен через rtpengine_enable: recheck_ticks = (unsigned)-1
    assert rtpengine._state(1, rtpengine.MAX_RECHECK_TICKS) == "inactive"
    assert rtpengine._state(1, -1) == "inactive"
    # выключен самим модулем: перепроверит через конечное число тиков
    assert rtpengine._state(1, 120) == "probing"
    assert rtpengine._state(None, None) == "unknown"


def test_rtpengine_socket_normalization():
    from app.services import rtpengine

    assert rtpengine.normalize_socket(" UDP:10.0.0.1:2223 ") == "udp:10.0.0.1:2223"
    assert rtpengine.normalize_socket(None) == ""


# --------------------------------------------------------------------------------------
# доверенные адреса (permissions)
# --------------------------------------------------------------------------------------


def test_address_prefix_len_from_dotted_mask():
    from app.services import address

    # в дампе маска подсети приходит в точечном виде, в таблице лежит длина префикса
    assert address._prefix_len("255.255.255.0", "10.0.0.0") == 24
    assert address._prefix_len("24") == 24
    assert address._prefix_len("") is None
    assert address._prefix_len("не маска") is None


def test_address_key_matches_db_row_and_mi_entry():
    from app.services import address

    db_row = {"grp": 1, "ip": "10.0.0.0", "mask": 24, "port": 0, "proto": "any"}
    mi_entry = {"grp": 1, "ip": "10.0.0.0", "mask": "255.255.255.0", "port": 0, "proto": "any"}
    assert address._key(**db_row) == address._key(**mi_entry)

    # одиночный адрес: в дампе маска приходит числом
    assert address._key(0, "10.0.0.5", 32, 5060, "UDP") == address._key(0, "10.0.0.5", "32", 5060, "udp")
    # разные группы не должны схлопываться
    assert address._key(1, "10.0.0.5", 32, 0, "any") != address._key(2, "10.0.0.5", 32, 0, "any")
