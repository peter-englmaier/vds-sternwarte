"""Overview of all orders.

Routes::

    GET  /obs_requests   obs_request_complete()  -> obs_request_complete.html
    GET  /order_history  order_history()         -> home.html
"""
from flask import render_template, request
from flask_login import current_user, login_required

from webapp.model.db import User, ObservationRequest, Observatory
from webapp.orders import orders  # blueprint object
from webapp.orders.constants import (
    ORDER_STATUS_LABELS,
    ORDER_STATUS_CREATED,
    ORDER_STATUS_WAITING,
    ORDER_STATUS_APPROVED,
    ORDER_STATUS_REJECTED,
    ORDER_STATUS_PU_ASSIGNED,
    ORDER_STATUS_PU_ACCEPTED,
)


# --------------------------------------------------------------------
# Observation Requests Gesamt
# --------------------------------------------------------------------

@orders.route("/obs_requests")
@login_required
def obs_request_complete():
    """Show all orders, sorted by request date.

    For the template, each order gets ``status_label``,
    ``display_poweruser_name``, ``display_observatory_name`` and
    ``display_requester_name``.

    :return: rendered ``obs_request_complete.html``.
    """
    orders = ObservationRequest.query.order_by(ObservationRequest.request_date.asc()).all()

    for order in orders:
        # Status-Label
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")

        # Poweruser-Anzeige
        order.display_poweruser_name = "-"
        if order.request_poweruser_id:
            pwuser = User.query.get(order.request_poweruser_id)
            if pwuser:
                order.display_poweruser_name = pwuser.display_name()

        # Observatorium-Anzeige
        order.display_observatory_name = "-"
        if order.request_observatory_id:
            observatory = Observatory.query.get(order.request_observatory_id)
            if observatory:
                order.display_observatory_name = observatory.name

        # Antragsteller-Anzeige
        order.display_requester_name = order.name if order.name else "-"
        if not order.display_requester_name and order.user_id:
            user = User.query.get(order.user_id)
            if user:
                full_name = f"{user.firstname or ''} {user.surname or ''}".strip()
                order.display_requester_name = full_name if full_name else user.name

    return render_template(
        "obs_request_complete.html",
        orders=orders,
        ORDER_STATUS_CREATED=ORDER_STATUS_CREATED,
        ORDER_STATUS_WAITING=ORDER_STATUS_WAITING,
        ORDER_STATUS_APPROVED=ORDER_STATUS_APPROVED,
        ORDER_STATUS_REJECTED=ORDER_STATUS_REJECTED,
        ORDER_STATUS_PU_ASSIGNED=ORDER_STATUS_PU_ASSIGNED,
        ORDER_STATUS_PU_ACCEPTED=ORDER_STATUS_PU_ACCEPTED,
    )

#Sortierung und Archivierung

@orders.route("/order_history")
def order_history():
    """Show the order history.

    .. warning:: ``Post`` and ``USER_ROLE_USER`` are not imported, so the route
       fails with a :exc:`NameError` (status 500) for logged-in users. It has
       no ``login_required``, and ``order_history.html`` does not exist.

    :return: rendered ``home.html`` for anonymous users.
    """
    if not current_user.is_authenticated or current_user.has_role(USER_ROLE_USER):
        return render_template("home.html")
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template("order_history.html", posts=posts)
