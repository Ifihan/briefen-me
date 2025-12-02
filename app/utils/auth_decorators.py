from functools import wraps
from flask import request, jsonify
import jwt
import os
from app.models.user import User


def jwt_optional(f):
    """Decorator for optional JWT authentication - attaches user if token is valid."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        request.current_user = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            try:
                payload = jwt.decode(
                    token,
                    os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
                    algorithms=['HS256']
                )
                user = User.query.get(payload['user_id'])
                if user:
                    request.current_user = user
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                pass

        return f(*args, **kwargs)

    return decorated_function