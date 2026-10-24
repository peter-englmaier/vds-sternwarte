"""Approver page: orders to approve and to assign to a poweruser.

The actions on this page are in webapp/orders/routes/approval.py.

Routes::

    GET  /approver  approver()  -> approver.html
"""
from collections import defaultdict
from datetime import date, timedelta

from flask import render_template
from flask_login import login_required

from webapp.main import main  # blueprint object
from webapp.model.db import db, ObservationRequest, PoweruserMeldung, User
from webapp.orders.constants import ORDER_STATUS_LABELS, ORDER_STATUS_WAITING, ORDER_STATUS_PU_REJECTED, \
    ORDER_STATUS_PU_ACCEPTED, ORDER_STATUS_APPROVED, ORDER_STATUS_PU_ASSIGNED
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Approver-Seite anzeigen
# --------------------------------------------------------------------
@main.route("/approver", methods=["GET"])
@login_required
@role_required("approver")
def approver():
    """Show the orders the approver has to handle, with the feedback of the
    powerusers.

    Lists orders in status waiting, approved, PU assigned, PU rejected and
    PU accepted. Assigned orders older than three days are hidden. Orders in
    status PU rejected are labeled "Action required" and come first.

    .. warning:: The line ``-order.request_date.timestamp()`` in the loop is a
       leftover expression without effect. The orders are not sorted by date.

    :return: rendered ``approver.html``.
    """
    cutoff_date = date.today() - timedelta(days=3)

    all_orders = (
        ObservationRequest.query
        .filter(ObservationRequest.status.in_([ORDER_STATUS_WAITING, ORDER_STATUS_APPROVED, ORDER_STATUS_PU_ASSIGNED, ORDER_STATUS_PU_REJECTED, ORDER_STATUS_PU_ACCEPTED]))
        .all()
    )
    all_orders = [order for order in all_orders
    if order.status != ORDER_STATUS_PU_ASSIGNED
    or order.request_date.date() >= cutoff_date
]
    # Action-required-Anträge ganz nach oben
    all_orders.sort(
    key=lambda order: order.status != ORDER_STATUS_PU_REJECTED
    )

    for order in all_orders:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")
        -order.request_date.timestamp()

        # Zugewiesener Poweruser kann Termin nicht mehr wahrnehmen
        if order.status == ORDER_STATUS_PU_REJECTED:
            order.status_label = "Action required"

        if order.request_poweruser_id:
            order.poweruser_name = User.query.get(order.request_poweruser_id).display_name()

    order_ids = [o.id for o in all_orders]

    pu_meldungen_by_order = defaultdict(list)
    if order_ids:
        rows = (
            db.session.query(
                PoweruserMeldung.observation_request_id,
                PoweruserMeldung.poweruser_user_id,
                PoweruserMeldung.availability,
                User.name,
                User.firstname,
                User.surname,
            )
            .join(User, User.id == PoweruserMeldung.poweruser_user_id)
            .filter(PoweruserMeldung.observation_request_id.in_(order_ids))
            .all()
        )

        for r in rows:
            display_name = User.query.get(r[1]).display_name()
            pu_meldungen_by_order[r.observation_request_id].append({
                "user_id": r.poweruser_user_id,
                "name": display_name or f"User {r.poweruser_user_id}",
                "availability": r.availability,
            })

    return render_template("approver.html", orders=all_orders, pu_meldungen_by_order=pu_meldungen_by_order)
