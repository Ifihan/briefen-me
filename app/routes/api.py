from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import current_user
from app import db
from app.models.url import URL
from app.services.url_validator import validate_url
from app.services.slug_generator import generate_slug_options

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/generate-slugs', methods=['POST'])
def generate_slugs():
    """
    Generate AI-powered slug options for a URL.
    Returns Server-Sent Events stream for real-time updates.
    """
    data = request.get_json()
    long_url = data.get('url')

    if not long_url:
        return jsonify({'error': 'URL is required'}), 400

    # Validate URL
    is_valid, error_message = validate_url(long_url)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    def generate():
        """Stream generation process updates."""
        try:
            # Use the slug generator service
            for update in generate_slug_options(long_url):
                yield f"data: {update}\n\n"
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@bp.route('/create-short-url', methods=['POST'])
def create_short_url():
    """Create a shortened URL with the selected slug."""
    data = request.get_json()
    long_url = data.get('url')
    slug = data.get('slug')

    if not long_url or not slug:
        return jsonify({'error': 'URL and slug are required'}), 400

    # Validate URL again
    is_valid, error_message = validate_url(long_url)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    # Check if slug already exists
    if URL.query.filter_by(slug=slug).first():
        return jsonify({'error': 'Slug already taken'}), 400

    # Create new URL entry
    user_id = current_user.id if current_user.is_authenticated else None
    new_url = URL(
        original_url=long_url,
        slug=slug,
        user_id=user_id
    )

    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        'success': True,
        'slug': slug,
        'short_url': request.host_url + slug,
        'original_url': long_url
    }), 201