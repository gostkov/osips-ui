"""Проверяем password flow по URL из OpenAPI, как его вызывает Swagger UI."""


def test_swagger_form_login_and_authenticated_request(client):
    schema = client.get("/openapi.json").json()
    flow = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]
    token_url = flow["tokenUrl"]
    assert token_url == "api/auth/token"  # относительный URL сохраняет ROOT_PATH за прокси
    response = client.post(token_url, data={"grant_type": "password", "username": "admin", "password": "admin-test-pass"})
    assert response.status_code == 200, response.text
    token = response.json()
    assert token["token_type"] == "bearer"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_swagger_rejects_wrong_password(client):
    response = client.post("/api/auth/token", data={"grant_type": "password", "username": "admin", "password": "wrong"})
    assert response.status_code == 401
