from flask import render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlparse
from webapp import bcrypt, db
from webapp.model.db import User, Post, Group
from webapp.users import users
from webapp.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                   ChangePasswordForm,
                                   RequestResetForm, ResetPasswordForm)
from webapp.users.utils import check_password_strength, save_picture, send_reset_email
from sqlalchemy import func
from webapp.orders.constants import USER_ROLE_GUEST


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")

        user = User(
            name=form.username.data,
            email=form.email.data,
            password=hashed_password,
            firstname=form.firstname.data,
            surname=form.surname.data,
            vds_number=form.vds_number.data,
        )


        guest_group = Group.query.filter_by(name=f"{USER_ROLE_GUEST}_group").first()
        if guest_group:
            user.groups.append(guest_group)
        else:

            flash("Systemfehler: Guest-Gruppe fehlt (setup_users?).", "danger")

        db.session.add(user)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Es ist ein Fehler aufgetreten: {e}. Bitte melden Sie sich beim Systemadministrator.", "error")
            return render_template("register.html", title="Register", form=form)

        flash("Ihr Benutzer ist registriert! Sie können sich jetzt anmelden", "success")
        return redirect(url_for("users.login"))

    return render_template("register.html", title="Register", form=form)

@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter( 
            func.upper(User.email) == form.email.data.upper()
        ).first()

        if not user:
           user = User.query.filter(
                func.upper(User.name) == form.email.data.upper()
            ).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            if not current_app.config.get('ALLOW_WEAK_PASSWORDS', False):
                password_is_strong, message = check_password_strength(form.password.data)
                if not password_is_strong:
                    flash(
                        f'Ihr Passwort muss aktualisiert werden. {message}',
                        'warning',
                    )
                    return redirect(url_for('users.account'))

            next_page = request.args.get('next', '').replace('\\', '')
            if next_page and not urlparse(next_page).netloc and not urlparse(next_page).scheme:
                return redirect(next_page)
            
            return redirect(url_for('main.home'))
        else:
            flash('Login nicht erfolgreich. Bitte prüfen Sie ihre Angaben!', 'danger')

    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    password_form = ChangePasswordForm(prefix='pw')
    if password_form.submit.data:
        if current_user.name == 'admin':
            flash('Der Benutzer admin kann sein Passwort hier nicht ändern.', 'danger')
            return redirect(url_for('users.account'))
        if password_form.validate_on_submit():
            if not bcrypt.check_password_hash(current_user.password, password_form.current_password.data):
                password_form.current_password.errors.append('Das aktuelle Passwort ist nicht korrekt.')
            else:
                if not current_app.config.get('ALLOW_WEAK_PASSWORDS', False):
                    password_is_strong, message = check_password_strength(
                        password_form.password.data,
                        current_password=password_form.current_password.data,
                    )
                    if not password_is_strong:
                        password_form.password.errors.append(message)
                if not password_form.password.errors:
                    current_user.password = bcrypt.generate_password_hash(
                        password_form.password.data
                    ).decode('utf-8')
                    current_user.session_version += 1
                    db.session.commit()
                    logout_user()
                    flash('Ihr Passwort wurde aktualisiert.', 'success')
                    return redirect(url_for('users.password_changed'))
    elif form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.name = form.username.data
        current_user.email = form.email.data
        current_user.firstname = form.firstname.data
        current_user.surname = form.surname.data
        current_user.vds_number = form.vds_number.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    if request.method == 'GET' or not form.submit.data:
        form.username.data = current_user.name
        form.email.data = current_user.email
        form.firstname.data = current_user.firstname
        form.surname.data = current_user.surname
        form.vds_number.data = current_user.vds_number
    if current_user.image_file == 'default.jpg':
        image_file = url_for('static', filename='default.jpg')
    else:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form,
                           password_form=password_form)

@users.route('/password_changed')
def password_changed():
    return render_template('password_changed.html', title='Passwort geändert')


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(name=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.session_version += 1
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
