from flask import Blueprint, request, jsonify, Response, stream_with_context, send_file, current_app
from flask_login import current_user, login_required
from app import db
from app.models.url import URL
from app.services.url_validator import validate_url
from app.services.slug_generator import generate_slug_options
import qrcode
from io import BytesIO

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

    # If AI thinking mode requires Gemini, ensure the GEMINI_API_KEY is configured
    ai_mode = current_app.config.get("AI_THINKING_MODE", "hardcoded")
    if ai_mode == "ai_generated" and not current_app.config.get("GEMINI_API_KEY"):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "AI is configured to generate slugs but GEMINI_API_KEY is not set. Please configure the GEMINI_API_KEY environment variable.",
                    "error_type": "missing_api_key",
                }
            ),
            400,
        )

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

        import re

        # Validate slug format and length (same rules as edit_slug)
        if not re.match(r"^[a-z0-9-]+$", slug):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Slug can only contain lowercase letters, numbers, and hyphens",
                    }
                ),
                400,
            )

        max_len = current_app.config.get("MAX_SLUG_LENGTH", 50)
        if len(slug) > max_len:
            return (
                jsonify({"success": False, "error": f"Slug must be {max_len} characters or less"}),
                400,
            )

        # Check if slug already exists
        if URL.query.filter_by(slug=slug).first():
            return jsonify({"success": False, "error": "Slug already taken"}), 400

        user_id = current_user.id if current_user.is_authenticated else None
        new_url = URL(original_url=normalized_url, slug=slug, user_id=user_id)

        db.session.add(new_url)
        db.session.commit()

        # Build short URL using configured BASE_URL if present, otherwise request.host_url
        base = current_app.config.get("BASE_URL") or request.host_url
        short_url = base.rstrip("/") + "/" + slug

        return (
            jsonify(
                {
                    "success": True,
                    "url_id": new_url.id,
                    "slug": slug,
                    "short_url": short_url,
                    "original_url": normalized_url,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500


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

        base = current_app.config.get("BASE_URL") or request.host_url
        short_url = base.rstrip("/") + "/" + new_slug

        return (
            jsonify(
                {
                    "success": True,
                    "old_slug": old_slug,
                    "new_slug": new_slug,
                    "short_url": short_url,
                    "url_id": url_id,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "error": f"An error occurred: {str(e)}"}),
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
        base = current_app.config.get("BASE_URL") or request.host_url
        short_url = base.rstrip("/") + "/" + url_obj.slug

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
        if img_io:
            img_io.close()
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500
