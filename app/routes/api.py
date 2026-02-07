from flask import Blueprint, request, jsonify, Response, stream_with_context, send_file
from flask_login import current_user, login_required
from app import db
from app.models.url import URL
from app.models.bio import BioPage, BioLink
from app.services.url_validator import validate_url
from app.services.slug_generator import generate_slug_options
from app.services.storage_service import upload_avatar, delete_avatar, get_avatar
from app.utils.auth_decorators import jwt_optional, subadmin_required
import qrcode
from io import BytesIO
import re
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/generate-slugs", methods=["POST"])
def generate_slugs():
    """
    Generate AI-powered slug options for a URL.
    Returns Server-Sent Events stream for real-time updates.
    """
    data = request.get_json()
    long_url = data.get("url")

    if not long_url:
        return jsonify({"error": "URL is required"}), 400

    # Validate URL
    is_valid, error_message, normalized_url = validate_url(long_url)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    def generate():
        """Stream generation process updates."""
        try:
            # Use the slug generator service with normalized URL
            for update in generate_slug_options(normalized_url):
                yield f"data: {update}\n\n"
        except Exception as e:
            db.session.rollback()
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.route("/create-short-url", methods=["POST"])
@jwt_optional
def create_short_url():
    """Create a shortened URL with the selected slug."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400

        long_url = data.get("url")
        slug = data.get("slug")

        if not long_url or not slug:
            return (
                jsonify({"success": False, "error": "URL and slug are required"}),
                400,
            )

        # Validate URL again and get normalized version
        is_valid, error_message, normalized_url = validate_url(long_url)
        if not is_valid:
            return jsonify({"success": False, "error": error_message}), 400

        # Check if slug already exists
        if URL.query.filter_by(slug=slug).first():
            return jsonify({"success": False, "error": "Slug already taken"}), 400

        # Support both JWT and session-based auth
        user_id = None
        if hasattr(request, 'current_user') and request.current_user:
            user_id = request.current_user.id
        elif current_user.is_authenticated:
            user_id = current_user.id

        new_url = URL(original_url=normalized_url, slug=slug, user_id=user_id)

        db.session.add(new_url)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "url_id": new_url.id,
                    "slug": slug,
                    "short_url": request.host_url + slug,
                    "original_url": normalized_url,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        logger.exception("Error creating short URL")
        return jsonify({"success": False, "error": "An internal error occurred while creating the short URL"}), 500


@bp.route("/edit-slug/<int:url_id>", methods=["PUT"])
def edit_slug(url_id):
    """Edit the slug of an existing shortened URL."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400

        new_slug = data.get("slug")

        if not new_slug:
            return jsonify({"success": False, "error": "New slug is required"}), 400

        import re

        if not re.match(r"^[a-z0-9-]+$", new_slug):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Slug can only contain lowercase letters, numbers, and hyphens",
                    }
                ),
                400,
            )

        if len(new_slug) > 50:
            return (
                jsonify(
                    {"success": False, "error": "Slug must be 50 characters or less"}
                ),
                400,
            )

        url_obj = URL.query.get_or_404(url_id)

        if current_user.is_authenticated:
            if url_obj.user_id != current_user.id:
                return (
                    jsonify(
                        {"success": False, "error": "Unauthorized to edit this link"}
                    ),
                    403,
                )
        else:
            if url_obj.user_id is not None:
                return (
                    jsonify(
                        {"success": False, "error": "Unauthorized to edit this link"}
                    ),
                    403,
                )
        existing = URL.query.filter_by(slug=new_slug).first()
        if existing and existing.id != url_id:
            return (
                jsonify({"success": False, "error": "This slug is already taken"}),
                400,
            )

        old_slug = url_obj.slug
        url_obj.slug = new_slug
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "old_slug": old_slug,
                    "new_slug": new_slug,
                    "short_url": request.host_url + new_slug,
                    "url_id": url_id,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.exception("Error editing slug")
        return (
            jsonify({"success": False, "error": "An internal error occurred while editing the slug"}),
            500,
        )


@bp.route("/qrcode/<int:url_id>", methods=["GET"])
@login_required
def generate_qrcode(url_id):
    """Generate QR code for a shortened URL."""
    img_io = None
    try:
        # Get the URL and verify ownership
        url_obj = URL.query.get_or_404(url_id)

        # Check if the user owns this URL
        if url_obj.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        # Generate the short URL
        short_url = request.host_url + url_obj.slug

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(short_url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)

        # Return image file
        return send_file(
            img_io,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"qrcode-{url_obj.slug}.png",
        )

    except Exception as e:
        db.session.rollback()
        logger.exception("Error generating QR code")
        if img_io:
            img_io.close()
        return jsonify({"success": False, "error": "An internal error occurred while generating the QR code"}), 500


@bp.route("/analytics/<slug>", methods=["GET"])
@jwt_optional
def get_analytics(slug):
    """Get analytics data for a shortened URL."""
    try:
        # Support both JWT and session-based auth
        user = None
        if hasattr(request, 'current_user') and request.current_user:
            user = request.current_user
        elif current_user.is_authenticated:
            user = current_user

        if not user:
            return jsonify({"success": False, "error": "Not found"}), 404

        url_obj = URL.query.filter_by(slug=slug).first()
        if not url_obj or url_obj.user_id != user.id:
            return jsonify({"success": False, "error": "Not found"}), 404

        days_param = request.args.get("days")
        days = int(days_param) if days_param else None

        from app.services.analytics_service import get_analytics as fetch_analytics

        data = fetch_analytics(url_obj.id, days=days)

        return jsonify({
            "success": True,
            "slug": url_obj.slug,
            "original_url": url_obj.original_url,
            "total_clicks": url_obj.click_count,
            "analytics": data,
        }), 200

    except Exception as e:
        logger.exception("Error fetching analytics")
        return jsonify({"success": False, "error": "An internal error occurred while fetching analytics"}), 500


@bp.route("/edit-url/<int:url_id>", methods=["PUT"])
@subadmin_required
def edit_url(url_id):
    """Edit the destination URL of an existing shortened URL. Sub-admin only."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400

        new_url = data.get("original_url")

        if not new_url:
            return jsonify({"success": False, "error": "New URL is required"}), 400

        # Validate the new URL
        is_valid, error_message, normalized_url = validate_url(new_url)
        if not is_valid:
            return jsonify({"success": False, "error": error_message}), 400

        url_obj = URL.query.get_or_404(url_id)

        # Check ownership - sub-admins can only edit their own links
        if url_obj.user_id != current_user.id:
            return (
                jsonify(
                    {"success": False, "error": "Unauthorized to edit this link"}
                ),
                403,
            )

        old_url = url_obj.original_url
        url_obj.original_url = normalized_url
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "old_url": old_url,
                    "new_url": normalized_url,
                    "url_id": url_id,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.exception("Error editing URL")
        return (
            jsonify({"success": False, "error": "An internal error occurred while editing the URL"}),
            500,
        )


# --- Bio Page API Endpoints ---


def _get_bio_user():
    """Get authenticated user from JWT or session. Returns user or None."""
    if hasattr(request, 'current_user') and request.current_user:
        return request.current_user
    if current_user.is_authenticated:
        return current_user
    return None


USERNAME_RE = re.compile(r"^[a-z0-9_-]{3,30}$")
VALID_THEMES = {"default", "dark", "minimal", "colorful"}


@bp.route("/bio", methods=["GET"])
@jwt_optional
def get_bio():
    """Get current user's bio page and links."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": True, "bio_page": None}), 200

    links = BioLink.query.filter_by(
        bio_page_id=page.id
    ).order_by(BioLink.position).all()

    return jsonify({
        "success": True,
        "bio_page": {
            "id": page.id,
            "username": page.username,
            "display_name": page.display_name,
            "bio": page.bio,
            "avatar_url": page.avatar_url,
            "theme": page.theme,
            "links": [
                {
                    "id": link.id,
                    "title": link.title,
                    "url": link.url,
                    "position": link.position,
                    "is_active": link.is_active,
                    "click_count": link.click_count,
                }
                for link in links
            ],
        },
    }), 200


@bp.route("/bio", methods=["POST"])
@jwt_optional
def create_bio():
    """Create a new bio page."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    existing = BioPage.query.filter_by(user_id=user.id).first()
    if existing:
        return jsonify({"success": False, "error": "Bio page already exists. Use PUT to update."}), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request data"}), 400

    username = data.get("username", "").strip().lower()
    if not username or not USERNAME_RE.match(username):
        return jsonify({
            "success": False,
            "error": "Username must be 3-30 characters: lowercase letters, numbers, underscores, hyphens",
        }), 400

    if BioPage.query.filter_by(username=username).first():
        return jsonify({"success": False, "error": "Username already taken"}), 400

    display_name = data.get("display_name", "").strip()[:100] or None
    bio = data.get("bio", "").strip()[:500] or None
    theme = data.get("theme", "default")
    if theme not in VALID_THEMES:
        theme = "default"

    try:
        page = BioPage(
            user_id=user.id,
            username=username,
            display_name=display_name,
            bio=bio,
            theme=theme,
        )
        db.session.add(page)
        db.session.commit()

        return jsonify({
            "success": True,
            "bio_page": {
                "id": page.id,
                "username": page.username,
                "display_name": page.display_name,
                "bio": page.bio,
                "avatar_url": page.avatar_url,
                "theme": page.theme,
                "links": [],
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception("Error creating bio page")
        return jsonify({"success": False, "error": "Failed to create bio page"}), 500


@bp.route("/bio", methods=["PUT"])
@jwt_optional
def update_bio():
    """Update bio page settings."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Bio page not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request data"}), 400

    try:
        if "username" in data:
            new_username = data["username"].strip().lower()
            if not USERNAME_RE.match(new_username):
                return jsonify({
                    "success": False,
                    "error": "Username must be 3-30 characters: lowercase letters, numbers, underscores, hyphens",
                }), 400
            existing = BioPage.query.filter_by(username=new_username).first()
            if existing and existing.id != page.id:
                return jsonify({"success": False, "error": "Username already taken"}), 400
            page.username = new_username

        if "display_name" in data:
            page.display_name = data["display_name"].strip()[:100] or None

        if "bio" in data:
            page.bio = data["bio"].strip()[:500] or None

        if "theme" in data and data["theme"] in VALID_THEMES:
            page.theme = data["theme"]

        db.session.commit()

        return jsonify({
            "success": True,
            "bio_page": {
                "id": page.id,
                "username": page.username,
                "display_name": page.display_name,
                "bio": page.bio,
                "avatar_url": page.avatar_url,
                "theme": page.theme,
            },
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error updating bio page")
        return jsonify({"success": False, "error": "Failed to update bio page"}), 500


@bp.route("/bio/avatar", methods=["POST"])
@jwt_optional
def upload_bio_avatar():
    """Upload avatar image for bio page."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Bio page not found. Create one first."}), 404

    if "avatar" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["avatar"]
    if not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    try:
        file_data = file.read()
        old_avatar = page.avatar_url

        blob_name = upload_avatar(file_data, file.filename, file.content_type)

        # Store blob name in database
        page.avatar_url = blob_name
        db.session.commit()

        # Delete old avatar after successful update
        if old_avatar:
            delete_avatar(old_avatar)

        # Return URL path for the avatar endpoint
        avatar_url = f"/api/avatar/{blob_name}"

        return jsonify({
            "success": True,
            "avatar_url": avatar_url,
        }), 200

    except (ValueError, RuntimeError) as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.exception("Error uploading avatar")
        return jsonify({"success": False, "error": f"Upload failed: {e}"}), 500


@bp.route("/avatar/<path:blob_name>", methods=["GET"])
def serve_avatar(blob_name):
    """Serve avatar image from Google Cloud Storage."""
    file_data, content_type = get_avatar(blob_name)

    if not file_data:
        return jsonify({"error": "Avatar not found"}), 404

    return Response(file_data, mimetype=content_type)


@bp.route("/bio/links", methods=["POST"])
@jwt_optional
def create_bio_link():
    """Add a new link to bio page."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Bio page not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request data"}), 400

    title = data.get("title", "").strip()
    url = data.get("url", "").strip()

    if not title or not url:
        return jsonify({"success": False, "error": "Title and URL are required"}), 400

    if len(title) > 100:
        return jsonify({"success": False, "error": "Title must be 100 characters or less"}), 400

    try:
        # Set position to end of list - use count for better performance
        link_count = BioLink.query.filter_by(bio_page_id=page.id).count()

        link = BioLink(
            bio_page_id=page.id,
            title=title,
            url=url,
            position=link_count,
        )
        db.session.add(link)
        db.session.commit()

        return jsonify({
            "success": True,
            "link": {
                "id": link.id,
                "title": link.title,
                "url": link.url,
                "position": link.position,
                "is_active": link.is_active,
                "click_count": link.click_count,
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception("Error creating bio link")
        return jsonify({"success": False, "error": "Failed to create link"}), 500


@bp.route("/bio/links/<int:link_id>", methods=["PUT"])
@jwt_optional
def update_bio_link(link_id):
    """Update a bio link."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Not found"}), 404

    link = BioLink.query.filter_by(id=link_id, bio_page_id=page.id).first()
    if not link:
        return jsonify({"success": False, "error": "Link not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request data"}), 400

    try:
        if "title" in data:
            title = data["title"].strip()
            if not title:
                return jsonify({"success": False, "error": "Title cannot be empty"}), 400
            link.title = title[:100]

        if "url" in data:
            url = data["url"].strip()
            if not url:
                return jsonify({"success": False, "error": "URL cannot be empty"}), 400
            link.url = url

        if "is_active" in data:
            link.is_active = bool(data["is_active"])

        db.session.commit()

        return jsonify({
            "success": True,
            "link": {
                "id": link.id,
                "title": link.title,
                "url": link.url,
                "position": link.position,
                "is_active": link.is_active,
                "click_count": link.click_count,
            },
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error updating bio link")
        return jsonify({"success": False, "error": "Failed to update link"}), 500


@bp.route("/bio/links/<int:link_id>", methods=["DELETE"])
@jwt_optional
def delete_bio_link(link_id):
    """Delete a bio link."""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Not found"}), 404

    link = BioLink.query.filter_by(id=link_id, bio_page_id=page.id).first()
    if not link:
        return jsonify({"success": False, "error": "Link not found"}), 404

    try:
        db.session.delete(link)
        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error deleting bio link")
        return jsonify({"success": False, "error": "Failed to delete link"}), 500


@bp.route("/bio/links/reorder", methods=["PUT"])
@jwt_optional
def reorder_bio_links():
    """Reorder bio links. Expects JSON: {"order": [{"id": 1, "position": 0}, ...]}"""
    user = _get_bio_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    page = BioPage.query.filter_by(user_id=user.id).first()
    if not page:
        return jsonify({"success": False, "error": "Not found"}), 404

    data = request.get_json()
    if not data or "order" not in data:
        return jsonify({"success": False, "error": "Order data required"}), 400

    try:
        for item in data["order"]:
            link = BioLink.query.filter_by(
                id=item["id"], bio_page_id=page.id
            ).first()
            if link:
                link.position = item["position"]

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error reordering bio links")
        return jsonify({"success": False, "error": "Failed to reorder links"}), 500


@bp.route("/bio/links/<int:link_id>/click", methods=["POST"])
def track_bio_link_click(link_id):
    """Track a click on a bio link. Public endpoint, no auth required."""
    link = BioLink.query.get(link_id)
    if not link:
        return jsonify({"success": False}), 404

    try:
        link.click_count += 1
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"success": False}), 500
