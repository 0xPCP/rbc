from flask import Flask
from .config import Config
from .extensions import db, login_manager, bcrypt, csrf, mail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.clubs import clubs_bp
    from .routes.admin import admin_bp
    from .routes.strava import strava_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(clubs_bp, url_prefix='/clubs')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(strava_bp, url_prefix='/strava')
    app.register_blueprint(api_bp, url_prefix='/api')

    from datetime import datetime
    from .version import __version__
    from .utils import club_theme_vars

    app.jinja_env.globals['club_theme_vars'] = club_theme_vars

    @app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow(), 'version': __version__}

    # Start weather auto-cancel scheduler (skipped in testing)
    if not app.config.get('TESTING'):
        from .scheduler import init_scheduler
        init_scheduler(app)

    return app
