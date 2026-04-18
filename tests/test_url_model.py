import pytest
from sqlalchemy.exc import IntegrityError

from app.models.url import URL


def test_url_creation(app, db):
    url = URL(original_url="https://example.com", slug="test-slug")
    db.session.add(url)
    db.session.commit()
    assert url.id is not None
    assert url.original_url == "https://example.com"
    assert url.slug == "test-slug"
    assert url.click_count == 0


def test_url_slug_unique(app, db):
    url1 = URL(original_url="https://example.com", slug="unique-slug")
    db.session.add(url1)
    db.session.commit()

    url2 = URL(original_url="https://other.com", slug="unique-slug")
    db.session.add(url2)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_url_increment_clicks(app, db):
    url = URL(original_url="https://example.com", slug="click-test")
    db.session.add(url)
    db.session.commit()
    assert url.click_count == 0
    url.increment_clicks()
    assert url.click_count == 1


def test_url_repr(app):
    url = URL(original_url="https://example.com", slug="repr-test")
    assert "repr-test" in repr(url)
