from datetime import datetime

from flask import current_app

from app import db


class URL(db.Model):
    """URL model for shortened links."""

    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def increment_clicks(self) -> None:
        """Increment the click counter with error handling."""
        try:
            self.click_count += 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if current_app:
                current_app.logger.error(f"Failed to increment click count for {self.slug}: {str(e)}")
            raise

    def __repr__(self) -> str:
        return f"<URL {self.slug} -> {self.original_url[:50]}>"
