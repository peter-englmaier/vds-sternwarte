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
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Observation Requests Gesamt
# --------------------------------------------------------------------

## Obsolete???
## Should this list really be visible all users, including guests???
## Let's restrict to power users for the time being
@orders.route("/obs_requests")
@login_required
@role_required("poweruser")
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
