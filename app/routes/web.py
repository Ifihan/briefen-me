from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.url import URL
from app.models.bio import BioPage, BioLink
from app.services.email_service import send_password_reset_email
from app.services.analytics_service import record_click
from datetime import datetime
import jwt
import os

bp = Blueprint('web', __name__)


@bp.route('/')
def index():
    """Homepage with URL shortener form."""
    return render_template('index.html')


@bp.route('/@<username>')
def bio_page(username):
    """Public bio page."""
    page = BioPage.query.filter_by(username=username).first_or_404()
    links = BioLink.query.filter_by(
        bio_page_id=page.id, is_active=True
    ).order_by(BioLink.position).all()
    return render_template('bio_page.html', page=page, links=links)


@bp.route('/<slug>')
def redirect_to_url(slug):
    """Redirect short URL to original URL."""
    url = URL.query.filter_by(slug=slug).first_or_404()
    record_click(url, request, current_app)
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

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('web.login'))

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


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page - send password reset email."""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Always show success message (security best practice - don't reveal if email exists)
        if user:
            # Generate reset token
            reset_token = user.generate_reset_token()
            db.session.commit()

            # Send reset email
            email_sent = send_password_reset_email(user.email, reset_token)

            if not email_sent:
                # Log error but still show success to user
                flash('There was a problem sending the email. Please try again later.', 'error')
                return render_template('forgot_password.html')

        # Always show confirmation page (even if email doesn't exist)
        return render_template('forgot_password_confirmation.html', email=email)

    return render_template('forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page with token validation."""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))

    # Find user by reset token
    user = User.find_by_reset_token(token)

    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('web.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate password
        if not password:
            flash('Please enter a new password', 'error')
            return render_template('reset_password.html', token=token)

        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)

        # Update password and clear reset token
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()

        flash('Password reset successful! Please log in with your new password.', 'success')
        return redirect(url_for('web.login'))

    return render_template('reset_password.html', token=token)


@bp.route('/extension-auth')
def extension_auth():
    """Exchange JWT token for web session cookie (auto-login from extension)."""
    token = request.args.get('token')

    if not token:
        flash('Invalid authentication', 'error')
        return redirect(url_for('web.login'))

    try:
        payload = jwt.decode(
            token,
            os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            algorithms=['HS256']
        )
        user = User.query.get(payload['user_id'])

        if user:
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('web.dashboard'))

    except jwt.ExpiredSignatureError:
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('web.login'))
    except jwt.InvalidTokenError:
        flash('Authentication failed', 'error')
        return redirect(url_for('web.login'))

    flash('Authentication failed', 'error')
    return redirect(url_for('web.login'))


@bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('web.index'))


@bp.route('/create')
@login_required
def create():
    """Create new short link page for authenticated users."""
    return render_template('create.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their shortened URLs with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = URL.query.filter_by(user_id=current_user.id).order_by(
        URL.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    urls = pagination.items
    bio_page = BioPage.query.filter_by(user_id=current_user.id).first()
    return render_template('dashboard.html', urls=urls, pagination=pagination, bio_page=bio_page)


@bp.route('/bio/edit')
@login_required
def bio_editor():
    """Bio page editor."""
    page = BioPage.query.filter_by(user_id=current_user.id).first()
    links = []
    if page:
        links = BioLink.query.filter_by(
            bio_page_id=page.id
        ).order_by(BioLink.position).all()
    user_urls = URL.query.filter_by(user_id=current_user.id).order_by(URL.created_at.desc()).all()
    return render_template('bio_editor.html', page=page, links=links, user_urls=user_urls)


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


@bp.route('/analytics/<slug>')
@login_required
def analytics(slug):
    """Analytics page for a shortened URL."""
    url = URL.query.filter_by(slug=slug).first_or_404()

    if url.user_id != current_user.id:
        abort(404)

    return render_template('analytics.html', url=url)


@bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')


@bp.route('/sitemap.xml')
def sitemap():
    """Generate dynamic XML sitemap for SEO."""
    pages = []

    # Static pages (public only)
    static_pages = [
        {'loc': url_for('web.index', _external=True), 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': url_for('web.privacy', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    pages.extend(static_pages)

    # Generate sitemap XML
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in pages:
        sitemap_xml.append('  <url>')
        sitemap_xml.append(f'    <loc>{page["loc"]}</loc>')
        sitemap_xml.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
        sitemap_xml.append(f'    <priority>{page["priority"]}</priority>')
        sitemap_xml.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        sitemap_xml.append('  </url>')

    sitemap_xml.append('</urlset>')

    return Response('\n'.join(sitemap_xml), mimetype='application/xml')


@bp.route('/robots.txt')
def robots():
    """Serve robots.txt file."""
    robots_txt = f"""# robots.txt for Briefen.me
# Allow all crawlers to index public pages

User-agent: *
Allow: /
Allow: /static/

# Disallow authentication and user-specific pages
Disallow: /login
Disallow: /signup
Disallow: /logout
Disallow: /dashboard
Disallow: /create
Disallow: /forgot-password
Disallow: /reset-password
Disallow: /delete/
Disallow: /analytics/
Disallow: /bio/edit
Disallow: /api/

# Sitemap location
Sitemap: {url_for('web.sitemap', _external=True)}

# Crawl-delay for polite crawling
Crawl-delay: 1
"""
    return Response(robots_txt, mimetype='text/plain')