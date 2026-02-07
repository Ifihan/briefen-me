import hashlib
import threading
import logging
from datetime import datetime, timedelta

import requests
from user_agents import parse as parse_user_agent
from sqlalchemy import func

from app import db
from app.models.click import Click

logger = logging.getLogger(__name__)


def hash_ip(ip_address, salt):
    """Hash an IP address with SHA-256 and a salt for privacy."""
    if not ip_address:
        return None
    return hashlib.sha256(f"{salt}{ip_address}".encode()).hexdigest()


def parse_device_info(ua_string):
    """Parse user-agent string and return (device_type, browser)."""
    if not ua_string:
        return "unknown", "Unknown"

    ua = parse_user_agent(ua_string)

    if ua.is_bot:
        device_type = "bot"
    elif ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "unknown"

    browser = ua.browser.family or "Unknown"

    return device_type, browser


def resolve_geolocation(click_id, ip_address, app):
    """Resolve IP to country/city using ip-api.com in a background thread."""
    try:
        with app.app_context():
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                params={"fields": "status,country,city"},
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    click = db.session.get(Click, click_id)
                    if click:
                        click.country = data.get("country", "Unknown")
                        click.city = data.get("city", "Unknown")
                        db.session.commit()
    except Exception as e:
        logger.warning(f"Geolocation lookup failed for click {click_id}: {e}")


def record_click(url, request_obj, app):
    """
    Record a click event for a URL.
    Creates the Click row synchronously, then resolves geolocation in background.
    Also increments url.click_count in the same commit.
    """
    ip_address = request_obj.remote_addr
    salt = app.config.get("IP_HASH_SALT", "default-salt")
    ua_string = request_obj.headers.get("User-Agent", "")
    referrer = request_obj.referrer

    ip_hashed = hash_ip(ip_address, salt)
    device_type, browser = parse_device_info(ua_string)

    click = Click(
        url_id=url.id,
        ip_hash=ip_hashed,
        referrer=referrer,
        user_agent=ua_string,
        device_type=device_type,
        browser=browser,
    )

    url.click_count += 1
    db.session.add(click)
    db.session.commit()

    if ip_address:
        thread = threading.Thread(
            target=resolve_geolocation,
            args=(click.id, ip_address, app._get_current_object()),
            daemon=True,
        )
        thread.start()

    return click


def get_analytics(url_id, days=None):
    """
    Aggregate analytics data for a URL.
    If days is provided, filter to last N days. Otherwise return all-time data.
    """
    query = Click.query.filter_by(url_id=url_id)

    since = None
    if days:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Click.clicked_at >= since)

    total_clicks = query.count()

    # Clicks over time (grouped by date)
    clicks_over_time_q = db.session.query(
        func.date(Click.clicked_at).label("date"),
        func.count(Click.id).label("count"),
    ).filter(Click.url_id == url_id)
    if since:
        clicks_over_time_q = clicks_over_time_q.filter(Click.clicked_at >= since)
    clicks_over_time = (
        clicks_over_time_q.group_by(func.date(Click.clicked_at))
        .order_by(func.date(Click.clicked_at))
        .all()
    )

    # Top referrers
    referrers_q = db.session.query(
        Click.referrer,
        func.count(Click.id).label("count"),
    ).filter(Click.url_id == url_id, Click.referrer.isnot(None))
    if since:
        referrers_q = referrers_q.filter(Click.clicked_at >= since)
    referrers = (
        referrers_q.group_by(Click.referrer)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )

    # Device breakdown
    devices_q = db.session.query(
        Click.device_type,
        func.count(Click.id).label("count"),
    ).filter(Click.url_id == url_id)
    if since:
        devices_q = devices_q.filter(Click.clicked_at >= since)
    devices = (
        devices_q.group_by(Click.device_type)
        .order_by(func.count(Click.id).desc())
        .all()
    )

    # Browser breakdown
    browsers_q = db.session.query(
        Click.browser,
        func.count(Click.id).label("count"),
    ).filter(Click.url_id == url_id)
    if since:
        browsers_q = browsers_q.filter(Click.clicked_at >= since)
    browsers = (
        browsers_q.group_by(Click.browser)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )

    # Country breakdown
    countries_q = db.session.query(
        Click.country,
        func.count(Click.id).label("count"),
    ).filter(Click.url_id == url_id, Click.country.isnot(None))
    if since:
        countries_q = countries_q.filter(Click.clicked_at >= since)
    countries = (
        countries_q.group_by(Click.country)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )

    return {
        "total_clicks": total_clicks,
        "clicks_over_time": [
            {"date": str(row.date), "count": row.count} for row in clicks_over_time
        ],
        "referrers": [
            {"referrer": row.referrer or "Direct", "count": row.count}
            for row in referrers
        ],
        "devices": [
            {"device": row.device_type or "unknown", "count": row.count}
            for row in devices
        ],
        "browsers": [
            {"browser": row.browser or "Unknown", "count": row.count}
            for row in browsers
        ],
        "countries": [
            {"country": row.country or "Unknown", "count": row.count}
            for row in countries
        ],
    }
