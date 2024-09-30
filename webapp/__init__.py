from flask import Flask
from flask_admin import Admin
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy.exc import OperationalError

from .config import Config
from .database import db
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

    #from webapp.admin.routes import admin
    from webapp.users.routes import users
    from webapp.posts.routes import posts
    from webapp.main.routes import main
    from webapp.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)


    # setup admin user, if name and password are set
    # always reset password to configured password
    pwd_complex = len(config_class.ADMIN_USER) > 3 \
        and len(config_class.ADMIN_USER) > 3 \
        and sum(c.isupper() for c in config_class.ADMIN_PASSWORD) > 0 \
        and sum(c.islower() for c in config_class.ADMIN_PASSWORD) > 0 \
        and sum(c.isdigit() for c in config_class.ADMIN_PASSWORD) > 0

    try:
        if pwd_complex:
            from webapp.models import User, Group, Role
            ctx=app.app_context()
            ctx.push()
            admin_user=User.query.filter_by(name=config_class.ADMIN_USER).first()
            hashed_password = bcrypt.generate_password_hash(config_class.ADMIN_PASSWORD).decode('utf-8')
            if admin_user:
                admin_user.password = hashed_password
                admin_user.email = config_class.ADMIN_EMAIL
                db.session.commit()
            else:
                print(f"INFO: Create new admin user {config_class.ADMIN_USER}")
                admin_user = User(name=config_class.ADMIN_USER, email=config_class.ADMIN_EMAIL, password=hashed_password)
                db.session.add(admin_user)
                db.session.commit()

            # add admin group, if not present, and assign to admin user
            admin_group=Group.query.filter_by(name="admin").first()
            if not admin_group:
                admin_group = Group(name="admin")
                admin_user.groups.append(admin_group)
                db.session.add(admin_group)
                db.session.add(admin_user)
                db.session.commit()
            elif admin_group not in admin_user.groups:
                admin_user.groups.append(admin_group)
                db.session.add(admin_user)
                db.session.commit()

            # add admin role, if not present, and assign to admin group
            admin_role=Role.query.filter_by(name="admin").first()
            if not admin_role:
                admin_role = Role(name="admin")
                admin_group.roles.append(admin_role)
                db.session.add(admin_role)
                db.session.add(admin_group)
                db.session.commit()
            elif admin_role not in admin_group.roles:
                admin_group.roles.append(admin_role)
                db.session.add(admin_group)
                db.session.commit()

            db.session.commit()
            ctx.pop()
        else:
            print("WARNING: password is not complex enough, not setting up admin user")
    except OperationalError:
        print("WARNING: Database not initialized")

    return app
