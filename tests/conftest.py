import pytest

from app import create_app
from app import db as _db
from app.models.user import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False
    SERVER_NAME = "localhost"
    IP_HASH_SALT = "test-salt"
    GCS_BUCKET_NAME = None
    GCS_PROJECT_ID = None
    RATELIMIT_ENABLED = False


@pytest.fixture(scope="function")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app, db):
    u = User(email="test@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    response = client.post(
        "/login", data={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code in (200, 302), f"Login failed: {response.status_code}"
    return client
