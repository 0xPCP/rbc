import sys
from flask import Flask, request, session
from flask_login import current_user
from .config import Config
from .extensions import db, login_manager, bcrypt, csrf, mail, babel


SUPPORTED_LANGUAGES = ['en', 'fr', 'es', 'it', 'nl', 'de', 'pt']

LANGUAGE_NAMES = {
    'en': 'English',
    'fr': 'Français',
    'es': 'Español',
    'it': 'Italiano',
    'nl': 'Nederlands',
    'de': 'Deutsch',
    'pt': 'Português',
}


def get_locale():
    if current_user.is_authenticated and current_user.language:
        return current_user.language
    lang = session.get('language')
    if lang and lang in SUPPORTED_LANGUAGES:
        return lang
    return request.accept_languages.best_match(SUPPORTED_LANGUAGES, default='en')


def _strftime_filter(value, fmt):
    """Cross-platform strftime: replaces %-d/%-I (Linux) with %#d/%#I on Windows."""
    if sys.platform == 'win32':
        fmt = fmt.replace('%-', '%#')
    return value.strftime(fmt)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.clubs import clubs_bp
    from .routes.admin import admin_bp
    from .routes.strava import strava_bp
    from .routes.api import api_bp
    from .routes.media import media_bp
    from .routes.user_rides import user_rides_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(clubs_bp, url_prefix='/clubs')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(strava_bp, url_prefix='/strava')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(media_bp)
    app.register_blueprint(user_rides_bp, url_prefix='/my-rides')

    from datetime import datetime
    from .version import __version__
    from .utils import club_theme_vars

    app.jinja_env.globals['club_theme_vars'] = club_theme_vars
    app.jinja_env.filters['strftime'] = _strftime_filter

    @app.context_processor
    def inject_globals():
        from flask_babel import get_locale as _get_locale
        return {
            'now': datetime.utcnow(),
            'version': __version__,
            'current_locale': str(_get_locale() or 'en'),
            'languages': LANGUAGE_NAMES,
        }

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
        # CSP: allow same-origin + Bootstrap/Google Fonts CDNs already in use
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "frame-src https://ridewithgps.com https://www.youtube.com https://player.vimeo.com; "
            "connect-src 'self';"
        )
        return response

    # Start weather auto-cancel scheduler (skipped in testing)
    if not app.config.get('TESTING'):
        from .scheduler import init_scheduler
        init_scheduler(app)

    return app
