"""Create a new order.

Routes::

    POST  /actionhandler  actionhandler()  -> create_order.html or redirect
"""
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import User, ObservationRequest, ObservatoryReservation, Observatory
from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import ObservationRequestHead
from webapp.orders.constants import ORDER_STATUS_CREATED, ORDER_STATUS_WAITING
from webapp.orders.orderservices import init_new_order_service
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Beobachtungsantrag erstellen, abschicken, sichern oder anzeigen
# --------------------------------------------------------------------
@orders.route("/actionhandler", methods=["POST"])
@login_required
@role_required("user")
def actionhandler():
    """Handle the buttons of the order overview and of the new-order form.

    The form field ``action`` selects what happens:

    * ``create_order``: show an empty form for a new order.
    * ``submit_order``: submit the order ``order_id`` for approval
      (status waiting).
    * ``save_order``: create a new order from the form, reserve the requested
      date and continue with editing the positions.

    :return: rendered ``create_order.html`` or a redirect.
    :raises Forbidden: if ``submit_order`` targets an order of another user.
    """
    action = request.form.get("action")
    order_id = request.form.get("order_id")
    form = ObservationRequestHead()

    # Start with new observation request
    if action == "create_order":
        order = init_new_order_service()
        form = ObservationRequestHead(obj=order)
        return render_template("create_order.html", form=form, order_id=None)

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
        return redirect("/orders")

    # Read entries from gui and save as new observation request (no positions so far)
    if action == "save_order":
        try:
            order_head = ObservationRequest()
            order_head.user_id = current_user.id
            order_head.request_date = form.request_date.data
            order_head.request_observatory_id = form.observatory_name.data
            observatory = Observatory.query.get(order_head.request_observatory_id)
            order_head.name = current_user.display_name() # form.requester_name.data
            poweruser_index = form.poweruser_name.data
            if poweruser_index != '':
                poweruser = next(( name for i, name in form.poweruser_name.choices if i == poweruser_index ), None)
                # poweruser now holds the display_name, not the name of the power user
                pw_users = User.by_role('poweruser')
                for pwuser in pw_users:
                    if pwuser.display_name() == poweruser:
                        order_head.request_poweruser_id = pwuser.id
                        break
            order_head.request_type = form.request_type.data
            order_head.remark = form.remark.data
            order_head.status = ORDER_STATUS_CREATED
            db.session.add(order_head)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Datum wurde nicht ausgewählt.  Bitte nochmal den Button <Neuen Antrag eingeben> drücken und ein Datum auswählen.", "warning")
            return redirect("/orders")

        # Reservation is created after the first commit so that order_head.id
        # is already assigned and ObservatoryReservation.__init__ can store it.
        reservation = None
        if form.request_date.data:
            reservation = ObservatoryReservation(order_head.request_date, observatory, order_head)

        try:
            if reservation:
                db.session.add(reservation)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(
                f"Datum kann nicht reserviert werden. Bitte anderes Datum wählen.",
                "danger",
            )
            return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))


        return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))

    return redirect("/orders")
