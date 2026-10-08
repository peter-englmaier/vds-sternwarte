# login_db_steps.py
# Steps for login tests using Flask test client with in-memory database.
# Scenarios must be tagged @db (see features/environment.py).

from behave import given, when, then
from webapp import bcrypt, db
from webapp.model.db import User


@given(u'weak passwords are allowed by configuration')
def allow_weak_passwords(context):
    context._flask_app.config['ALLOW_WEAK_PASSWORDS'] = True


@given(u'the following users are registered:')
def create_users_from_table(context):
    from webapp.model.db import Group
    has_group = 'group' in context.table.headings
    for row in context.table:
        hashed = bcrypt.generate_password_hash(row['password']).decode('utf-8')
        user = User(name=row['name'], email=row['email'], password=hashed)
        if has_group and row['group']:
            group = Group.query.filter_by(name=row['group']).first()
            if group:
                user.groups.append(group)
        db.session.add(user)
    db.session.commit()


@when(u'I post login with email "{email}" and password "{password}"')
def post_login(context, email, password):
    context.response = context.client.post('/login', data={
        'email': email,
        'password': password,
        'submit': True,
    }, follow_redirects=True)


@when(u'I change my password from "{old_password}" to "{new_password}"')
def change_password(context, old_password, new_password):
    context.response = context.client.post('/account', data={
        'pw-current_password': old_password,
        'pw-password': new_password,
        'pw-confirm_password': new_password,
        'pw-submit': 'Passwort ändern',
    }, follow_redirects=True)


@when(u'I register user "{username}" with password "{password}"')
def register_user(context, username, password):
    context.response = context.client.post('/register', data={
        'username': username,
        'email': f'{username}@example.com',
        'firstname': 'Test',
        'surname': 'User',
        'password': password,
        'confirm_password': password,
        'submit': 'Registrieren',
    }, follow_redirects=True)


@then(u'I am redirected to home')
def redirected_to_home(context):
    assert context.response.status_code == 200
    assert b'VdS Sternwarte' in context.response.data


@then(u'I am redirected to the profile page')
def redirected_to_profile(context):
    assert context.response.status_code == 200
    assert context.response.request.path == '/account'


@then(u'I am redirected to the password changed page')
def redirected_to_password_changed(context):
    assert context.response.status_code == 200
    assert context.response.request.path == '/password_changed'


@then(u'I am redirected to login')
def redirected_to_login(context):
    assert context.response.status_code == 200
    assert context.response.request.path == '/login'


@then(u'the response contains "{text}"')
def response_contains(context, text):
    encoded = text.encode()
    assert encoded in context.response.data, \
        f'"{text}" not found in response'
