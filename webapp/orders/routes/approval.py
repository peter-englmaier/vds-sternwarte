"""Approver and poweruser actions without a page of their own.

Triggered by buttons (partly HTMX) in approver.html and poweruser.html.

Routes::

    POST  /poweruser/<int:order_id>/pu_accept  pu_accept()                       -> redirect to poweruser page
    POST  /approver/assign_poweruser           approver_assign_poweruser()       -> HTML fragment (HTMX)
    POST  /approver/<int:order_id>/approve     approve_order()                   -> redirect to approver page
    GET   /approver/assign_poweruser_form      approver_assign_poweruser_form()  -> HTML fragment (HTMX)
"""
from flask import url_for, flash, redirect, request, abort
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import User, ObservationRequest, ObservatoryReservation
from webapp.orders import orders  # blueprint object
from webapp.orders.constants import ORDER_STATUS_PU_ACCEPTED, ORDER_STATUS_PU_ASSIGNED, ORDER_STATUS_APPROVED
from webapp.orders.mails import send_approve_email, send_accept_email, send_putime_email
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Poweruser weist sich Antrag zu
# --------------------------------------------------------------------
@orders.route("/poweruser/<int:order_id>/pu_accept", methods=["POST"])
@login_required
@role_required("poweruser")
def pu_accept(order_id):
    """Poweruser takes over an order assigned to them (status PU accepted).

    :param order_id: id of the order.
    :return: redirect to the poweruser page.
    :raises NotFound: if the order does not exist.
    :raises Forbidden: if the order is not in status PU assigned or is assigned
        to another poweruser.
    """
    order_head = ObservationRequest.query.get_or_404(order_id)
    if (
        order_head.status != ORDER_STATUS_PU_ASSIGNED
        or order_head.request_poweruser_id != current_user.id
    ):
        abort(403)

    order_head.status = ORDER_STATUS_PU_ACCEPTED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(
            f"Es ist ein Fehler aufgetreten: {e}. Bitte melden Sie sich beim Systemadministrator.",
            "danger",
        )
    else:
        flash("Antrag übernommen", "success")
    return redirect(url_for("main.poweruser"))


# --------------------------------------------------------------------
# Approver weißt einen Poweruser zu
# --------------------------------------------------------------------
@orders.route("/approver/assign_poweruser", methods=["POST"])
@login_required
@role_required("approver")
def approver_assign_poweruser():
    """Assign a poweruser to an order (HTMX request).

    Reads the form fields ``order_id`` and ``poweruser_user_id``, sets the status
    to PU assigned, confirms the reservation and sends the approval mail in the
    background (:func:`webapp.orders.mails.send_approve_email`).

    :return: HTML fragment that replaces the assignment slot, or an error
        fragment if a field is missing.
    :raises NotFound: if the order does not exist.
    """
    order_id = request.form.get("order_id", type=int)
    poweruser_user_id = request.form.get("poweruser_user_id", type=int)

    if not order_id or not poweruser_user_id:
        return f'<span id="pu-assign-feedback-{order_id or 0}" class="text-danger ms-2">Bitte Poweruser wählen</span>'

    order = ObservationRequest.query.get_or_404(order_id)
    try:
        order.request_poweruser_id = poweruser_user_id
        order.status = ORDER_STATUS_PU_ASSIGNED
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Es ist ein Fehler aufgetreten: {e}.")

    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first();
    if reservation:
        try:
            reservation.confirm()
            db.session.add(reservation)
            db.session.commit()
        except Exception as e:
            print(f"Es ist ein Fehler aufgetreten: {e}.")
            db.session.rollback()

    pu_user = User.query.get(poweruser_user_id)
    if pu_user:
        pu_name = pu_user.display_name()
    else:
        pu_name = None

    # notify requester and poweruser
    order_url = url_for('orders.show_order_positions', order_id=order_id, _external=True)
    send_approve_email.delay(order_id, current_user.id, order_url, None)

    return f"""

<span id="pu-assign-slot-{order_id}">
  <span class="text-success ms-2">
    Poweruser zugewiesen: <strong>{pu_name}</strong>
  </span>

  <button type="button"
          class="btn btn-sm btn-link ms-2 p-0 align-baseline"
          hx-get="{url_for('orders.approver_assign_poweruser_form')}?order_id={order_id}"
          hx-target="#pu-assign-slot-{order_id}"
          hx-swap="outerHTML">
    Neu zuweisen?
  </button>
</span>
"""


# --------------------------------------------------------------------
# Der Kontrolleur (Approver) akzeptiert Antrag
# --------------------------------------------------------------------
@orders.route("/approver/<int:order_id>/approve", methods=["POST"])
@login_required
@role_required("approver")
def approve_order(order_id):
    """Approver accepts an order.

    If the requester is a poweruser, the order is assigned to themselves
    (status PU assigned), the reservation is confirmed and
    :func:`~webapp.orders.mails.send_putime_email` is sent. Otherwise the status
    becomes approved and :func:`~webapp.orders.mails.send_accept_email` is sent.

    :param order_id: id of the order.
    :return: redirect to the approver page; the result is shown as flash message.
    """
    order_head = ObservationRequest.query.get(order_id)
    user=User.query.get(order_head.user_id)
    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first();
    is_pu = user.has_role('poweruser')
    done = False
    try:
        if is_pu:
            if reservation:
                reservation.confirm()
                db.session.add(reservation)
            order_head.status = ORDER_STATUS_PU_ASSIGNED
            order_head.request_poweruser_id = order_head.user_id
        else:
            order_head.status = ORDER_STATUS_APPROVED
        db.session.add(order_head)
        db.session.commit()
        done = True
        order_url = url_for('orders.show_order_positions', order_id=order_id, _external=True)
        if is_pu:
            send_putime_email.delay(order_id, current_user.id, order_url)
        else:
            send_accept_email.delay(order_id, current_user.id, order_url)
        flash(f"Antrag angenommen und Mail versendet", "success")
    except Exception as e:
        db.session.rollback()
        if done:
            flash(f"Antrag angenommen, aber Mail konnte nicht versendet werden. Fehler: {e}",
                  "danger")
        else:
            flash(f"Antrag kann nicht angenommen werden. Fehler: {e}.", "danger")

    return redirect(url_for("main.approver"))



@orders.route("/approver/assign_poweruser_form", methods=["GET"])
@login_required
@role_required("approver")
def approver_assign_poweruser_form():
    """Return the button to (re)assign a poweruser (HTMX request).

    The query parameter ``order_id`` names the order.

    :return: HTML fragment, or an error fragment with status 400 if
        ``order_id`` is missing.
    """
    order_id = request.args.get("order_id", type=int)
    if not order_id:
        return '<span class="text-danger">Fehlende order_id</span>', 400

    return f"""
    <span id="pu-assign-slot-{order_id}">
      <button id="pu-assign-btn-{order_id}"
              type="button"
              class="btn btn-sm btn-outline-primary mt-1"
              hx-post="{url_for('orders.approver_assign_poweruser')}"
              hx-include="#pu-select-{order_id} input, #order-id-{order_id}"
              hx-target="#pu-assign-slot-{order_id}"
              hx-swap="outerHTML">
        Poweruser zuweisen
      </button>
    </span>
    """
