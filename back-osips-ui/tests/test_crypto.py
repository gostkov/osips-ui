from app.core.crypto import decrypt, encrypt
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_secret_roundtrip():
    encrypted = encrypt("s3cret")
    assert encrypted != "s3cret"
    assert encrypted.startswith("enc:")
    assert decrypt(encrypted) == "s3cret"


def test_plain_value_is_returned_as_is():
    assert decrypt("legacy-plain") == "legacy-plain"
    assert encrypt(None) is None
    assert encrypt("") == ""


def test_password_hashing():
    digest = hash_password("qwerty123")
    assert verify_password("qwerty123", digest)
    assert not verify_password("wrong", digest)


def test_jwt_roundtrip():
    token = create_access_token("bob", "qa")
    payload = decode_access_token(token)
    assert payload["sub"] == "bob"
    assert payload["role"] == "qa"
