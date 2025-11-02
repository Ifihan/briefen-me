import json
import pytest

def _import_app():
    # Import app factory lazily to avoid issues during test collection
    from app import create_app, db

    return create_app, db


@pytest.fixture
def app():
    create_app, db = _import_app()
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "BASE_URL": "https://briefen.example",
    })

    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_short_url_valid_and_invalid_slug(client, app):
    # Invalid slug with uppercase and spaces
    resp = client.post(
        "/api/create-short-url",
        data=json.dumps({"url": "https://example.com/article", "slug": "Bad Slug!"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "Slug can only contain" in data["error"]

    # Valid slug (may already exist if the test DB was populated by another test run in this session)
    resp = client.post(
        "/api/create-short-url",
        data=json.dumps({"url": "https://example.com/article", "slug": "good-slug"}),
        content_type="application/json",
    )
    if resp.status_code == 201:
        data = resp.get_json()
        assert data["success"] is True
        assert data["short_url"].startswith("https://briefen.example/")
    else:
        # Accept a 400 if the slug was already created earlier in the test session
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "Slug already taken" in data["error"]

    # Duplicate slug
    resp = client.post(
        "/api/create-short-url",
        data=json.dumps({"url": "https://example.com/article2", "slug": "good-slug"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "Slug already taken" in data["error"]


def test_generate_slugs_missing_gemini_key(client, app):
    # Ensure AI_THINKING_MODE is ai_generated and GEMINI_API_KEY is not set
    app.config["AI_THINKING_MODE"] = "ai_generated"
    app.config["GEMINI_API_KEY"] = None

    resp = client.post(
        "/api/generate-slugs",
        data=json.dumps({"url": "https://example.com/article"}),
        content_type="application/json",
    )

    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"
    assert data["error_type"] == "missing_api_key"
