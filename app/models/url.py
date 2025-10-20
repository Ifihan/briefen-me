from datetime import datetime
from app import db


class URL(db.Model):
    """URL model for shortened links."""

    __tablename__ = 'urls'

    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def increment_clicks(self):
        """Increment the click counter."""
        self.click_count += 1
        db.session.commit()

    def __repr__(self):
        return f'<URL {self.slug} -> {self.original_url[:50]}>'