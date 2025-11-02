from __future__ import annotations

from typing import Optional, Type

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class: Type[Config] = Config) -> Flask:
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"

    @app.teardown_appcontext
    def shutdown_session(exception: Optional[BaseException] = None) -> None:
        """Remove database session at the end of the request or when the application shuts down."""
        db.session.remove()

    # Register blueprints
    from app.routes import api, web

    app.register_blueprint(web.bp)
    app.register_blueprint(api.bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id: int) -> Optional["User"]:  # noqa: F821 - forward ref to User
    # Import at runtime when needed to avoid circular imports
    from app.models.user import User

    return User.query.get(int(user_id))
