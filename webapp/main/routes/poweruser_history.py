"""Order history of the powerusers.

Routes::

    GET  /poweruser_order_history  poweruser_order_history()  -> poweruser_history.html
"""
from flask import render_template
from flask_login import current_user, login_required

from webapp.main import main  # blueprint object
from webapp.model.db import ObservationRequest, User
from webapp.orders.constants import ORDER_STATUS_PU_REJECTED, ORDER_STATUS_PU_ACCEPTED, ORDER_STATUS_PU_ASSIGNED
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Historie der Poweruser-Anträge anzeigen
# --------------------------------------------------------------------
@main.route("/poweruser_order_history")
@login_required
@role_required("poweruser")
def poweruser_order_history():
    """Show all orders that were assigned to a poweruser, newest first.

    Orders in status PU assigned, PU rejected and PU accepted are split into
    those of the current user and those of other powerusers.

    :return: rendered ``poweruser_history.html``.
    """
    all_orders = (
        ObservationRequest.query
        .filter(
            ObservationRequest.status.in_([
                ORDER_STATUS_PU_ASSIGNED,
                ORDER_STATUS_PU_REJECTED,
                ORDER_STATUS_PU_ACCEPTED,
            ])
        )
        .order_by(ObservationRequest.request_date.desc())
        .all()
    )

    own_orders = []
    others_orders = []

    for order in all_orders:
        if order.request_poweruser_id:
            pu_user = User.query.get(order.request_poweruser_id)
            order.poweruser_name = (
                pu_user.display_name()
                if pu_user
                else None
            )
        else:
            order.poweruser_name = None

        if order.request_poweruser_id == current_user.id:
            own_orders.append(order)
        else:
            others_orders.append(order)

    return render_template(
        "poweruser_history.html",
        own_orders=own_orders,
        others_orders=others_orders
    )
