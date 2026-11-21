"""Create a new order.

Routes::

    POST  /actionhandler  actionhandler()  -> edit_order_pos.html or redirect
"""
from flask import render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import ObservationRequest
from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import ObservationRequestPositionsForm
from webapp.orders.constants import ORDER_STATUS_CREATED, ORDER_STATUS_WAITING
from webapp.orders.orderservices import (
    get_user_preference_service,
    default_positions,
    position_data,
    group_blocks,
    posted_block_numbers,
    set_position_choices,
    apply_head,
    save_positions_service,
    submit_order_service,
    order_form_problems,
    prepare_reservation_service,
    error_reference,
    save_failed_message,
    reservation_error_message,
)
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Beobachtungsantrag erstellen, abschicken, sichern oder anzeigen
# --------------------------------------------------------------------
@orders.route("/actionhandler", methods=["POST"])
@login_required
@role_required("user")
def actionhandler():
    """Handle the buttons of the order overview and of the new-order page.

    The form field ``action`` selects what happens:

    * ``create_order``: show the page for a new order with head and positions.
    * ``submit_order``: submit the order ``order_id`` for approval
      (status waiting).
    * ``save_order``: create a new order with its positions from the form,
      reserve the requested date and continue on the edit page.
    * ``submit_new_order``: create the order like ``save_order`` and submit it
      for approval right away.

    If date, observatory or a telescope is missing, the page is shown again
    with the entered data and no order is created.

    :return: rendered ``edit_order_pos.html`` or a redirect.
    :raises Forbidden: if ``submit_order`` targets an order of another user.
    """
    action = request.form.get("action")
    order_id = request.form.get("order_id")
    form = None  # set below for a new order that is shown (again)
    blocks = None

    # Start with new observation request
    if action == "create_order":
        form = ObservationRequestPositionsForm()
        observatory_id = form.head.observatory_name.data  # preset if there is only one
        position_items = default_positions(observatory_id)
        form.process(data={
            "head": {
                "requester_name": current_user.display_name(),
                "observatory_name": observatory_id,
            },
            "positions": position_data(position_items),
        })
        set_position_choices(form, observatory_id)
        blocks = group_blocks([1] * len(position_items))

    # User submits order to get the approval
    if action == "submit_order":
        order_head = ObservationRequest.query.get(order_id)
        if order_head.user_id != current_user.id:
            abort(403)
        try:
            order_head.status = ORDER_STATUS_WAITING
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Datum wurde nicht ausgefüllt","danger")
        return redirect(url_for("orders.show_orders"))

    # Read head and positions from gui and save them as new observation request
    if action in ("save_order", "submit_new_order"):
        form = ObservationRequestPositionsForm(request.form)
        problems = order_form_problems(form)
        if problems:
            for message in problems:
                flash(message, "warning")
            set_position_choices(form, form.head.observatory_name.data)
            blocks = group_blocks(posted_block_numbers(request.form, len(form.positions)))

    # Show the page for a new order (empty, or again with missing data)
    if blocks is not None:
        return render_template(
            "edit_order_pos.html",
            expert_mode=get_user_preference_service(current_user.id, "expert_mode", "False"),
            form=form,
            order_id=None,
            blocks=blocks,
        )

    if action in ("save_order", "submit_new_order"):
        try:
            order_head = ObservationRequest()
            order_head.user_id = current_user.id
            order_head.name = current_user.display_name()
            apply_head(order_head, form.head)
            order_head.status = ORDER_STATUS_CREATED
            db.session.add(order_head)
            db.session.flush()  # assigns order_head.id for the positions
            save_positions_service(form, order_head.id, request.form)
            db.session.commit()
        except Exception:
            db.session.rollback()
            reference = error_reference()
            current_app.logger.exception(
                "[%s] Neuer Antrag von Benutzer %s konnte nicht gespeichert werden", reference, current_user.id)
            flash(save_failed_message("Der Antrag", reference), "danger")
            return redirect(url_for("orders.show_orders"))

        # Reservation is created after the first commit so that order_head.id
        # is already assigned and ObservatoryReservation.__init__ can store it.
        requested_date = order_head.request_date  # still readable after a rollback
        order_id_for_log = order_head.id
        reservation, message = prepare_reservation_service(order_head)
        if reservation is None:
            db.session.rollback()
            flash(message, "warning")
            return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            reference = error_reference()
            current_app.logger.exception(
                "[%s] Reservierung für Antrag %s konnte nicht gespeichert werden", reference, order_id_for_log)
            flash(reservation_error_message(exc, requested_date, reference), "danger")
            return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))

        if action == "submit_new_order":
            for message, category in submit_order_service(order_head.id):
                flash(message, category)
            return redirect(url_for("orders.show_orders"))

        flash("Deine Eingaben sind gespeichert!", "success")
        return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))

    return redirect(url_for("orders.show_orders"))
