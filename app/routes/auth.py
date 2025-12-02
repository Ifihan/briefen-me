from flask import Blueprint, request, jsonify
from app.models.user import User
from datetime import datetime, timedelta
import jwt
import os

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login', methods=['POST'])
def api_login():
    """API endpoint for extension login - returns JWT token."""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        # Generate JWT token with 30-day expiry
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'), algorithm='HS256')

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email
            }
        }), 200

    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401


@bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify if a JWT token is still valid."""
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'No token provided'}), 401

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(
            token,
            os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            algorithms=['HS256']
        )
        user = User.query.get(payload['user_id'])

        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email
                }
            }), 200

        return jsonify({'success': False, 'error': 'User not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401


@bp.route('/logout', methods=['POST'])
def api_logout():
    """Logout endpoint (client-side token removal)."""
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200