"""Order overview of the current user.

Routes::

    GET   /orders                              show_orders()   -> orders.html
    POST  /orders/<int:order_id>/copy_order    copy_order()    -> redirect to /orders
    POST  /orders/<int:order_id>/delete_order  delete_order()  -> redirect to /orders
"""
from datetime import date, timedelta

from flask import render_template, flash, redirect, abort
from flask_login import current_user, login_required

from webapp.model.db import User, ObservationRequest, ObservatoryReservation
from webapp.orders import orders  # blueprint object
from webapp.orders.constants import ORDER_STATUS_LABELS, ORDER_STATUS_CREATED, ORDER_STATUS_REJECTED
from webapp.orders.orderservices import copy_order_service, delete_order_service
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Beobachtungsantrag bearbeiten
# --------------------------------------------------------------------
@orders.route("/orders", methods=["GET"])
@login_required
@role_required("user")
def show_orders():
    """Show the orders of the current user.

    Only orders whose request date is at most three days in the past are listed.
    For the template, each order gets ``status_label``, ``date_is_reserved``,
    ``date_info`` and, if a poweruser is assigned, ``poweruser_name``.

    :return: rendered ``orders.html``.
    """
    cutoff_date = date.today() - timedelta(days=3)
    user_orders = ObservationRequest.query.filter_by(user_id=current_user.id).filter(ObservationRequest.request_date >= cutoff_date).order_by(ObservationRequest.request_date.desc()).all()
    for order in user_orders:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")
        reservation = ObservatoryReservation.query.filter_by(observation_request_id=order.id).first();
        if reservation:
            order.date_is_reserved = True
            order.date_info = reservation
        else:
            order.date_is_reserved = False
            order.date_info = order.request_date.strftime('%d.%m.%Y')
        pwuser = User.query.get(order.request_poweruser_id)
        if pwuser:
            order.poweruser_name = pwuser.display_name()
    return render_template("orders.html", title="Teleskopzeit Beantragung", orders=user_orders)


# --------------------------------------------------------------------
# Beobachtungsantrag kopieren
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/copy_order", methods=["POST"])
@login_required
@role_required("user")
def copy_order(order_id):
    """Copy an order of the current user.

    :param order_id: id of the order to copy.
    :return: redirect to the order overview; the result is shown as flash message.
    :raises NotFound: if the order does not exist.
    :raises Forbidden: if the order belongs to another user.
    """
    order = ObservationRequest.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)

    rc, message = copy_order_service(order_id)
    flash(message, "success" if rc == 0 else "danger")
    return redirect("/orders")


# --------------------------------------------------------------------
# Beobachtungsantrag löschen
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/delete_order", methods=["POST"])
@login_required
@role_required("user")
def delete_order(order_id):
    """Delete an order of the current user.

    Only orders in status created or rejected can be deleted.

    :param order_id: id of the order to delete.
    :return: redirect to the order overview; the result is shown as flash message.
    :raises NotFound: if the order does not exist.
    :raises Forbidden: if the order belongs to another user or has another status.
    """
    order = ObservationRequest.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    if order.status not in {ORDER_STATUS_CREATED, ORDER_STATUS_REJECTED}:
        abort(403)

    rc, message = delete_order_service(order_id)
    flash(message, "success" if rc == 0 else "danger")
    return redirect("/orders")
