from flask import Flask
from flask_admin import Admin
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

from .config import Config
from .database import db
from webapp.setup_users import setup_users
from webapp.admin.utils import init_admin


bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
login_manager.session_protection = "strong"
mail = Mail()
admin = Admin()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(
        SESSION_COOKIE_SECURE=False, # needs to be false, so we can run without https locally
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    db.init_app(app)
    migrate = Migrate(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    init_admin(app, admin) # setup admin views

    @app.before_request
    def set_global_variables():
        from .global_vars import set_global_vars
        set_global_vars()

    #from webapp.admin.routes import admin
    from webapp.users.routes import users
    from webapp.posts.routes import posts
    from webapp.main.routes import main
    from webapp.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    setup_users(app, bcrypt)

    return app
