from uuid import uuid4

import pytest


def login(client, username, password):
    response = client.post('/api/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize('password', ['a' * 73, 'я' * 37, '😀' * 19])
def test_oversized_password_is_rejected_by_all_write_endpoints(client, admin_headers, password):
    username = 'password-' + uuid4().hex
    rejected = client.post('/api/users', headers=admin_headers, json={'username': username, 'password': password})
    assert rejected.status_code == 422
    assert '72' in rejected.json()['detail'][0]['msg']
    created = client.post('/api/users', headers=admin_headers, json={'username': username, 'password': 'initial-password'})
    assert created.status_code == 201
    user_id = created.json()['id']
    try:
        headers = login(client, username, 'initial-password')
        assert client.put(f'/api/users/{user_id}', headers=admin_headers, json={'password': password}).status_code == 422
        assert client.post('/api/auth/change-password', headers=headers, json={
            'current_password': 'initial-password', 'new_password': password,
        }).status_code == 422
        login(client, username, 'initial-password')
    finally:
        client.delete(f'/api/users/{user_id}', headers=admin_headers)


def test_72_byte_passwords_work_for_create_update_and_change(client, admin_headers):
    username = 'boundary-' + uuid4().hex
    created = client.post('/api/users', headers=admin_headers, json={'username': username, 'password': 'a' * 72})
    assert created.status_code == 201
    user_id = created.json()['id']
    try:
        login(client, username, 'a' * 72)
        assert client.put(f'/api/users/{user_id}', headers=admin_headers, json={'password': 'я' * 36}).status_code == 200
        headers = login(client, username, 'я' * 36)
        assert client.post('/api/auth/change-password', headers=headers, json={
            'current_password': 'я' * 36, 'new_password': '😀' * 18,
        }).status_code == 200
        login(client, username, '😀' * 18)
    finally:
        client.delete(f'/api/users/{user_id}', headers=admin_headers)
