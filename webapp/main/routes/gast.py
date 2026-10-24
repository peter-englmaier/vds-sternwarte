"""Activate new users (guests and users without a group).

Routes::

    GET   /gast          gast()          -> gast.html
    POST  /gast/approve  gast_approve()  -> redirect to /gast
"""
from flask import render_template, request, url_for, redirect, flash, abort
from flask_login import current_user, login_required

from webapp.main import main  # blueprint object
from webapp.model.db import db, User, Group
from webapp.orders.constants import USER_ROLE_ADMIN, USER_ROLE_APPROVER, USER_ROLE_USER, USER_ROLE_GUEST


# --------------------------------------------------------------------
# Neue Benutzer anzeigen
# --------------------------------------------------------------------
@main.route("/gast", methods=["GET"])
@login_required
def gast():
    """Show all users waiting for activation: members of the guest group and
    users without any group.

    :return: rendered ``gast.html``.
    :raises Forbidden: if the current user is neither admin nor approver.
    """

    if not (
        current_user.has_role(USER_ROLE_ADMIN)
        or current_user.has_role(USER_ROLE_APPROVER)
    ):
        abort(403)

    guest_group = Group.query.filter_by(
        name=f"{USER_ROLE_GUEST}_group"
    ).first()

    pending_users = []

    if guest_group:
        pending_users = (
            User.query.join(User.groups)
            .filter(Group.id == guest_group.id)
            .all()
        )

    #Benutzer ohne Gruppenzuordnung
    no_group = [u for u in User.query.all() if not u.groups]
    pending_ids = {u.id for u in pending_users}
    pending_users.extend([u for u in no_group if u.id not in pending_ids])

    return render_template(
        "gast.html",
        title="Neue Benutzer freischalten",
        pending_users=pending_users,
    )


# --------------------------------------------------------------------
# Benutzer freischalten
# --------------------------------------------------------------------
@main.route("/gast/approve", methods=["POST"])
@login_required
def gast_approve():
    """Activate a user: remove them from the guest group and add them to the
    user group.

    Expects the form field ``user_id``.

    :return: redirect to ``/gast``.
    :raises Forbidden: if the current user is neither admin nor approver.
    :raises NotFound: if the user does not exist.
    """

    if not (
        current_user.has_role(USER_ROLE_ADMIN)
        or current_user.has_role(USER_ROLE_APPROVER)
    ):
        abort(403)

    user_id = request.form.get("user_id", type=int)
    if not user_id:
        flash("Fehlende user_id", "danger")
        return redirect(url_for("main.gast"))

    user = User.query.get_or_404(user_id)

    guest_group = Group.query.filter_by(
        name=f"{USER_ROLE_GUEST}_group"
    ).first()
    user_group = Group.query.filter_by(
        name=f"{USER_ROLE_USER}_group"
    ).first()

    if not user_group:
        flash("Systemfehler: user_group existiert nicht.", "danger")
        return redirect(url_for("main.gast"))

    if guest_group and guest_group in user.groups:
        user.groups.remove(guest_group)

    if user_group not in user.groups:
        user.groups.append(user_group)

    db.session.commit()

    flash(f"{user.name} wurde freigeschaltet.", "success")
    return redirect(url_for("main.gast"))
