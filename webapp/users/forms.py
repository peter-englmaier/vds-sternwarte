from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask import current_app
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from flask_login import current_user
from webapp.model.db import User
from webapp.users.utils import check_password_strength, PASSWORD_REQUIREMENTS
from sqlalchemy import func


class RegistrationForm(FlaskForm):
    username = StringField('Benutzername',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-Mail',
                        validators=[DataRequired(), Email()])
    firstname = StringField('Vorname',validators=[DataRequired(), Length(min=2, max=20)])
    surname = StringField('Nachname',validators=[DataRequired(), Length(min=2, max=20)])
    vds_number = IntegerField('VDS Mitgliedsnummer')
    password = PasswordField('Passwort', validators=[DataRequired()],
                             description=PASSWORD_REQUIREMENTS)
    confirm_password = PasswordField('Passwort wiederholen',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    def validate_password(self, password):
        if not current_app.config.get('ALLOW_WEAK_PASSWORDS', False):
            password_is_strong, message = check_password_strength(password.data)
            if not password_is_strong:
                raise ValidationError(message)

    def validate_username(self, username):
        user = User.query.filter_by(name=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('E-Mail oder Benutzername',
                        validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')


class UpdateAccountForm(FlaskForm):
    username = StringField('Benutzername',
                           validators=[DataRequired(), Length(min=2, max=20)])
    firstname = StringField('Vorname')
    surname = StringField('Nachname')
    ##FIXME: use CSS to remove spinners from IntegerField
    vds_number = IntegerField('VDS Mitgliedsnummer')
    email = StringField('E-Mail',
                        validators=[DataRequired(), Email()])
    picture = FileField('Profilbild ändern', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Aktualisieren')

    def validate_username(self, username):
        if username.data != current_user.name:
#            user = User.query.filter_by(name=username.data).first()
            user = User.query.filter(
                func.upper(User.name) == username.data.upper()
            ).first()

            if user:
                raise ValidationError('Dieser Benutzername wird bereits verwendet, bitte anderen wählen!')

    def validate_email(self, email):
        if email.data != current_user.email:
#            user = User.query.filter_by(email=email.data).first()
            user = User.query.filter(
                func.upper(User.email) == email.data.upper()
            ).first()
            if user:
                raise ValidationError('Diese E-Mail-Adresse wird bereits verwendet, bitte andere wählen!')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Aktuelles Passwort', validators=[DataRequired()])
    password = PasswordField('Neues Passwort', validators=[DataRequired()],
                             description=PASSWORD_REQUIREMENTS)
    confirm_password = PasswordField('Neues Passwort wiederholen',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Passwort ändern')


class RequestResetForm(FlaskForm):
    email = StringField('E-Mail',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Passwort-Rücksetzung anfordern')

    def validate_email(self, email):
#        user = User.query.filter_by(email=email.data).first()
        user = User.query.filter(
            func.upper(User.email) == email.data.upper()
        ).first()
        if user is None:
            raise ValidationError('Es gibt keine Anmeldung mit dieser E-Mail-Adresse, bitte erst registrieren!')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Passwort', validators=[DataRequired()])
    confirm_password = PasswordField('Passwort wiederholen',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Passwort zurücksetzen')
