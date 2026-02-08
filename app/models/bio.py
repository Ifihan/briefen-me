from datetime import datetime
from app import db
import re


class BioPage(db.Model):
    """Bio page model for link-in-bio feature."""

    __tablename__ = "bio_pages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.Text, nullable=True)
    theme = db.Column(db.String(20), default="default", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", backref=db.backref("bio_page", uselist=False))
    links = db.relationship(
        "BioLink",
        backref="bio_page",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="BioLink.position",
    )

    @property
    def avatar_display_url(self):
        """Get the display URL for the avatar."""
        if not self.avatar_url:
            return None
        if self.avatar_url.startswith(("http://", "https://", "/")):
            return self.avatar_url
        return f"/api/avatar/{self.avatar_url}"

    def __repr__(self):
        return f"<BioPage @{self.username}>"


class BioLink(db.Model):
    """Individual link on a bio page."""

    __tablename__ = "bio_links"

    id = db.Column(db.Integer, primary_key=True)
    bio_page_id = db.Column(
        db.Integer, db.ForeignKey("bio_pages.id"), nullable=False, index=True
    )
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_social = db.Column(db.Boolean, default=False, nullable=False)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Social media platform patterns
    SOCIAL_PATTERNS = {
        'twitter': r'(twitter\.com|x\.com)',
        'linkedin': r'linkedin\.com',
        'github': r'github\.com',
        'instagram': r'instagram\.com',
        'facebook': r'facebook\.com',
        'youtube': r'youtube\.com',
        'tiktok': r'tiktok\.com',
        'discord': r'discord\.(gg|com)',
        'telegram': r't\.me',
        'whatsapp': r'(wa\.me|whatsapp\.com)',
        'snapchat': r'snapchat\.com',
        'reddit': r'reddit\.com',
        'pinterest': r'pinterest\.com',
        'twitch': r'twitch\.tv',
        'medium': r'medium\.com',
    }

    @property
    def social_platform(self):
        """Detect which social media platform this link belongs to."""
        if not self.is_social:
            return None

        url_lower = self.url.lower()
        for platform, pattern in self.SOCIAL_PATTERNS.items():
            if re.search(pattern, url_lower):
                return platform
        return 'other'

    def __repr__(self):
        return f"<BioLink {self.title} -> {self.url[:50]}>"
