import json
import os
import sys

# Ensure project root is on sys.path so imports like `config` resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db


def run():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "BASE_URL": "https://briefen.example",
    })

    with app.app_context():
        db.create_all()

        client = app.test_client()

        print('1) Test create-short-url with invalid slug')
        resp = client.post(
            "/api/create-short-url",
            data=json.dumps({"url": "https://example.com/article", "slug": "Bad Slug!"}),
            content_type="application/json",
        )
        print('status:', resp.status_code)
        print('body:', resp.get_json())

        print('\n2) Test create-short-url with valid slug')
        resp = client.post(
            "/api/create-short-url",
            data=json.dumps({"url": "https://example.com/article", "slug": "good-slug"}),
            content_type="application/json",
        )
        print('status:', resp.status_code)
        print('body:', resp.get_json())

        print('\n3) Test generate-slugs with AI mode and missing GEMINI key')
        app.config['AI_THINKING_MODE'] = 'ai_generated'
        app.config['GEMINI_API_KEY'] = None
        resp = client.post(
            "/api/generate-slugs",
            data=json.dumps({"url": "https://example.com/article"}),
            content_type="application/json",
        )
        print('status:', resp.status_code)
        try:
            print('body:', resp.get_json())
        except Exception:
            print('body not JSON')


if __name__ == '__main__':
    run()
