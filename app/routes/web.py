from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.url import URL

bp = Blueprint('web', __name__)


@bp.route('/')
def index():
    """Homepage with URL shortener form."""
    return render_template('index.html')


@bp.route('/<slug>')
def redirect_to_url(slug):
    """Redirect short URL to original URL."""
    url = URL.query.filter_by(slug=slug).first_or_404()
    url.increment_clicks()
    return redirect(url.original_url)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('web.signup'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('web.dashboard'))

    return render_template('signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('web.index'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their shortened URLs."""
    urls = URL.query.filter_by(user_id=current_user.id).order_by(URL.created_at.desc()).all()
    return render_template('dashboard.html', urls=urls)


@bp.route('/delete/<int:url_id>', methods=['POST'])
@login_required
def delete_url(url_id):
    """Delete a shortened URL."""
    url = URL.query.get_or_404(url_id)

    if url.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('web.dashboard'))

    db.session.delete(url)
    db.session.commit()
    flash('URL deleted successfully', 'success')
    return redirect(url_for('web.dashboard'))