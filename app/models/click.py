from datetime import datetime
from app import db


class Click(db.Model):
    """Click model for tracking individual link clicks."""

    __tablename__ = "clicks"

    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(
        db.Integer, db.ForeignKey("urls.id"), nullable=False, index=True
    )
    clicked_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    ip_hash = db.Column(db.String(64), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    referrer = db.Column(db.Text, nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    browser = db.Column(db.String(100), nullable=True)

    url = db.relationship(
        "URL",
        backref=db.backref("clicks", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Click {self.id} for url_id={self.url_id}>"
