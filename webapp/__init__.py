from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from webapp.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
login_manager.session_protection = "strong"
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    db.init_app(app)
    migrate = Migrate(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from webapp.users.routes import users
    from webapp.posts.routes import posts
    from webapp.main.routes import main
    from webapp.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    # setup admin user, if username and password are set
    # always reset password to configured password
    try:
        pwd_complex = len(config_class.ADMIN_USER) > 3 \
            and len(config_class.ADMIN_USER) > 3 \
            and sum(c.isupper() for c in config_class.ADMIN_PASSWORD) > 0 \
            and sum(c.islower() for c in config_class.ADMIN_PASSWORD) > 0 \
            and sum(c.isdigit() for c in config_class.ADMIN_PASSWORD) > 0

        if pwd_complex:
            from webapp.models import User, Group
            ctx=app.app_context()
            ctx.push()
            admin=User.query.filter_by(username=config_class.ADMIN_USER).first()
            hashed_password = bcrypt.generate_password_hash(config_class.ADMIN_PASSWORD).decode('utf-8')
            if admin:
                print(f"INFO: User {config_class.ADMIN_USER} already exists - reset password and email")
                admin.password = hashed_password
                admin.email = config_class.ADMIN_EMAIL
                db.session.commit()
            else:
                print(f"INFO: Create new admin user {config_class.ADMIN_USER}")
                admin = User(username=config_class.ADMIN_USER, email=config_class.ADMIN_EMAIL, password=hashed_password)
                db.session.add(admin)
                db.session.commit()

            # add admin group, if not present, and assign to admin user
            group=Group.query.filter_by(groupname="admin").first()
            if not group:
                print('create new group')
                group = Group(groupname="admin")
                admin.group.append(group)
                db.session.add(group)
                db.session.add(admin)
                db.session.commit()
            elif group not in admin.groups:
                print('add to existing group')
                admin.group.append(group)
                db.session.add(admin)
                db.session.commit()

            db.session.commit()
            ctx.pop()
        else:
            print("WARNING: password is not complex enough, not setting up admin user")
    except Exception:
        pass

    return app
