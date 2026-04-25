# features/environment.py
use_selenium = True

from behave import fixture, use_fixture
from webapp.config import Config


# ---------------------------------------------------------------------------
# Selenium setup (used for scenarios WITHOUT the @db tag)
# ---------------------------------------------------------------------------
if use_selenium:
    from selenium import webdriver


# ---------------------------------------------------------------------------
# Flask test-client config (used for scenarios tagged @db)
# ---------------------------------------------------------------------------
class TestConfig:
    SECRET_KEY = 'test-secret-key-for-behave'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    TESTING = True
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_REPLYTO = None
    MAIL_DEBUG = False
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    RESERVATION_MAXTIME_MINUTES = 60
    RESERVATION_TIME_MINUTES = 30
    # Admin user created by setup_users(). Password must satisfy:
    # length >3, >8 chars, upper + lower + digit.
    ADMIN_USER = 'testadmin'
    ADMIN_EMAIL = 'admin@test.com'
    ADMIN_PASSWORD = 'TestAdmin1!'


def before_all(context):
    # Selenium driver for non-@db scenarios
    if use_selenium:
        context.driver = webdriver.Chrome()
        context.app_config = Config()

    # Flask test app — created ONCE to avoid duplicate blueprint registration
    # (Flask-Admin's module-level Admin() singleton accumulates views on each
    # create_app() call, causing "already registered" errors on the second call).
    from webapp import create_app, db as _db
    context._flask_app = create_app(TestConfig)
    context._flask_db = _db


def after_all(context):
    if use_selenium:
        try:
            context.driver.quit()
        except Exception:
            pass


def before_scenario(context, scenario):
    if 'db' in scenario.effective_tags:
        # Push an app context that stays alive for the whole scenario so that
        # step code can use db.session directly without extra context managers.
        context._app_ctx = context._flask_app.app_context()
        context._app_ctx.push()
        context._flask_db.create_all()
        # Populate roles and groups (user_group, admin_group, etc.) so
        # fixture steps can assign users to groups.
        from webapp.users.setup_users import setup_users
        setup_users()
        context.client = context._flask_app.test_client()


def after_scenario(context, scenario):
    if 'db' in scenario.effective_tags:
        context._flask_db.session.remove()
        context._flask_db.drop_all()
        context._app_ctx.pop()
