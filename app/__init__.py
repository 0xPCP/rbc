from flask import Flask
from .config import Config
from .extensions import db, login_manager, bcrypt, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.rides import rides_bp
    from .routes.admin import admin_bp
    from .routes.strava import strava_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(rides_bp, url_prefix='/rides')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(strava_bp, url_prefix='/strava')

    from datetime import datetime
    from .version import __version__

    @app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow(), 'version': __version__}

    return app
