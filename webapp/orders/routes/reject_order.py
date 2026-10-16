"""Approver rejects an order.

Routes::

    GET, POST  /approver/<int:order_id>/reject  reject_order()  -> reject_order.html or redirect
"""
from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import User, ObservationRequest, ObservationRequestPosition, ObservatoryReservation, Observatory
from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import RejectOrderForm
from webapp.orders.constants import ORDER_STATUS_LABELS, ORDER_STATUS_REJECTED
from webapp.orders.mails import send_reject_email
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Der Kontrolleur (Approver) weist Antrag zurück
# --------------------------------------------------------------------
@orders.route("/approver/<int:order_id>/reject", methods=["GET", "POST"])
@login_required
@role_required("approver")
def reject_order(order_id):
    """Show and process the form to reject an order.

    On submit, the reservation is cancelled, the status becomes rejected and the
    rejection mail with the optional explanation is sent in the background
    (:func:`webapp.orders.mails.send_reject_email`). Cancel returns to the
    approver page.

    :param order_id: id of the order.
    :return: rendered ``reject_order.html`` or a redirect to the approver page.
    :raises NotFound: if the order does not exist.
    """
    order_head = ObservationRequest.query.get_or_404(order_id)
    user=User.query.get(order_head.user_id)
    observatory = Observatory.query.get(order_head.request_observatory_id)
    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    positions = ObservationRequestPosition.query.filter_by(
    observation_request_id=order_id
).all()
    order_head.status_label = ORDER_STATUS_LABELS.get(order_head.status, "??")
    form = RejectOrderForm()
    if form.validate_on_submit():
        if form.data['submit']:
            done=False
            try:
                reservation.cancel()
                db.session.add(reservation)
                db.session.commit()
                order_head.status = ORDER_STATUS_REJECTED
                db.session.add(order_head)
                db.session.commit()
                done=True
                order_url = url_for('orders.show_order_positions', order_id=order_id, _external=True)
                send_reject_email.delay(order_id, current_user.id, order_url, form.data['info'])
                flash(f"Antrag abgelehnt und Mail versendet", "success")
                return redirect(url_for("main.approver"))
            except Exception as e:
                db.session.rollback()
                if done:
                    flash(f"Antrag abgelehnt, aber Mail konnte nicht versendet werden. Fehler: {e}",
                          "danger")
                else:
                    flash(f"Antrag kann nicht abgelehnt werden. Fehler: {e}.", "danger")

        elif form.data['cancel']:
            return redirect(url_for("main.approver"))

    elif request.method == 'GET':
        # formular befuellen (hier nichts?)
        pass
    return render_template('reject_order.html',
                           form=form, order=order_head, user=user, observatory=observatory, reservation=reservation, order_position=positions)
