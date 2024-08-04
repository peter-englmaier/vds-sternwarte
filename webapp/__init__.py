from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from webapp.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
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

    # setup admin user, if user name and password are set
    # always reset password to configured password
    try:
        upper = sum(c.isupper() for c in config_class.ADMIN_PASSWORD)
        lower = sum(c.islower() for c in config_class.ADMIN_PASSWORD)
        digit = sum(c.isdigit() for c in config_class.ADMIN_PASSWORD)
        if len(config_class.ADMIN_USER) > 3 and len(config_class.ADMIN_PASSWORD) > 10 and upper>0 and lower>0 and digit>0:
            from webapp.models import User
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
            ctx.pop()
        else:
            print("WARNING: password is not complex enough, not setting up admin user")
    except:
        print("WARNING: Database not initialized")

    return app
