import pytest
from app import create_app
from datetime import timedelta
from pathlib import Path

@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "DEBUG": True,
        "JWT_ALGORITHM": "RS256",
        "JWT_PUBLIC_KEY": Path("config/keys/public.pem").read_text(),
        "API_URL_PREFIX": "/desktops/v1"
    })

    # Other setup can go here
    # in case we need to access the app context wrap the code in a with block
    #    with app.app_context():

    yield app

    # Clean up / reset resources here if needed


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def no_jwt(monkeypatch):
  """Monkeypatch the JWT verification functions for tests"""
  monkeypatch.setattr("flask_jwt_extended.verify_jwt_in_request", lambda: print("Faking token verification"))


@pytest.fixture(scope="function", autouse=True)
def get_jwt_identity(monkeypatch):
  """Monkeypatch the JWT identity for tests"""
  monkeypatch.setattr("flask_jwt_extended.get_jwt_identity", lambda: "test")
