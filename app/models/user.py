from datetime import datetime, timedelta
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):
    """User model for registered users.

    Notes:
    - Passwords are stored as werkzeug password hashes.
    - Reset tokens are URL-safe strings with an expiry timestamp.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    urls = db.relationship("URL", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self) -> str:
        """Create a URL-safe reset token and set a 1 hour expiry."""
        import secrets

        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token: str) -> bool:
        """Verify the provided reset token is present and not expired."""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self) -> None:
        """Clear any stored reset token and expiry."""
        self.reset_token = None
        self.reset_token_expiry = None

    @staticmethod
    def find_by_reset_token(token: str) -> Optional["User"]:
        """Return the user with the given reset token, or None."""
        return User.query.filter_by(reset_token=token).first()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User {self.email}>"
