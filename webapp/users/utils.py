import os
import secrets
from PIL import Image
from flask import url_for, current_app, flash, redirect
from flask_mail import Message
from webapp import mail, Config
from functools import wraps
from flask_login import current_user


def check_password_strength(password, current_password=None, admin_policy=False):
    """Check password strength and return a validation message.

    :param password: Password to check.
    :param bool admin_policy: Whether to apply additional admin password checks.
    :param current_password: Current password; use ``None`` only when checking a
        configured password that has no existing value, such as initial admin setup.
    :return: A tuple containing whether the password is strong and the
        validation message for password changes.
    :rtype: tuple[bool, str]
    """
    if current_password is not None and password == current_password:
        return False, 'Das neue Passwort muss sich vom aktuellen Passwort unterscheiden.'

    has_digit = any(character.isdigit() for character in password) # check for digit (number)
    has_special_character = any( # check for at least one special character
        not character.isalnum() and not character.isspace() for character in password
    )
    is_strong = (
        len(password) >= 8 # check for standard user'S PW length
        and any(character.islower() for character in password) #check for lower caser letter
        and any(character.isupper() for character in password) # check for upper case letter
        and (has_digit or has_special_character) # check for at least one special character or one digit
    )
    if admin_policy:
        admin_checks = [len(password) >= 9, has_digit, has_special_character] # check for admin's pw length
        is_strong = is_strong and all(admin_checks)
        message = (
            'Das Admin-Passwort muss mindestens 9 Zeichen lang sein und '
            'Groß- und Kleinbuchstaben, eine Ziffer sowie ein Sonderzeichen enthalten.'
        )
    else:
        message = (
            'Das Passwort muss mindestens 8 Zeichen lang sein und '
            'Groß- und Kleinbuchstaben sowie eine Zahl oder ein Sonderzeichen enthalten.'
        )
    return is_strong, message


def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('users.login'))
            if not current_user.has_role(role_name) and not current_user.has_role("admin"):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f'''
    P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt. Sie sollte gehen an:
        {user.email}
    '''
        recipients = [user.email, Config.ADMIN_EMAIL]
    else:
        ps = ""
        recipients = [user.email]

    msg = Message('Password Reset Request',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
{ps}
'''
    mail.send(msg)