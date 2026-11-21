"""Edit an order and its positions.

Routes::

    GET, POST  /orders/<int:order_id>/edit  edit_order_pos()  -> edit_order_pos.html or redirect
"""
from flask import render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import ObservationRequest, ObservationRequestPosition
from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import (
    ObservationRequestPositionsForm,
    poweruser_query,
)
from webapp.orders.constants import (
    ORDER_STATUS_LABELS,
)
from webapp.orders.orderservices import (
    resolve_coordinates_service,
    get_user_preference_service,
    default_positions,
    position_data,
    group_blocks,
    set_position_choices,
    apply_head,
    save_positions_service,
    submit_order_service,
    prepare_reservation_service,
    error_reference,
    save_failed_message,
    reservation_error_message,
    can_edit_order,
)
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Beobachtungsantrag bearbeiten, Zeilen hinzufügen oder entfernen
# Der Kopfsatz muss schon vorhanden sein.
# Positionen werden, wenn vorhanden aus der DB geladen.
# Wenn keine Position existiert, wird eine neue mit zum Observatoruim passende
# Parametern erstellt
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("user")
def edit_order_pos(order_id):
    """Show and process the form to edit an order and its positions.

    The order head must already exist. On GET, the positions are loaded from the
    database; if there are none, a default position matching the observatory is
    created. On POST, the form field ``action`` selects what happens:

    * ``save_order``: save head and positions, update the reservation and show
      the form again.
    * ``submit_order``: save like ``save_order``, then submit the order for
      approval and freeze the reservation.
    * ``resolve_coordinates``: look up the coordinates of the targets and show
      the form again without saving.

    :param order_id: id of the order.
    :return: rendered ``edit_order_pos.html`` or a redirect.
    :raises Forbidden: if the order does not exist, belongs to another user
        (admins excepted) or is not a draft.
    """
    action = request.form.get("action")

    order_head = ObservationRequest.query.get(order_id)
    if order_head is None or not can_edit_order(order_head, current_user):
        abort(403)

    expert_mode = get_user_preference_service(current_user.id, "expert_mode", "False")
    selected_observatory_id = order_head.request_observatory_id

    # -------------------------
    # GET: Formular füllen
    # -------------------------
    if request.method == "GET":
        form = ObservationRequestPositionsForm()

        head_data = {
            "status": order_head.status,
            "status_label": ORDER_STATUS_LABELS.get(order_head.status, "??"),
            "request_date": order_head.request_date,
            "requester_name": order_head.name,
            "observatory_name": order_head.request_observatory_id,
            #"request_purpose": order_head.request_purpose,
            "poweruser_name": order_head.request_poweruser_id,
            "request_type": order_head.request_type,
            "remark": order_head.remark,
        }

        # sortiert laden, damit Block-/Zeilen-Reihenfolge stabil ist
        position_items = (
            ObservationRequestPosition.query.filter_by(observation_request_id=order_id)
            .order_by(
                ObservationRequestPosition.block_no,
                ObservationRequestPosition.row_in_block,
                ObservationRequestPosition.row_no,
                ObservationRequestPosition.id,
            )
            .all()
        )

        # Fallback: wenn keine Position existiert, eine Default-Zeile anlegen
        if len(position_items) == 0:
            position_items = default_positions(selected_observatory_id)

        form.process(
            data={
                "order_id": order_id,
                "head": head_data,
                "positions": position_data(position_items),
            }
        )

        # blocks-Struktur für Template: row_indices bezieht sich auf form.positions[]
        blocks = group_blocks([getattr(pos, "block_no", 1) or 1 for pos in position_items])

        set_position_choices(form, selected_observatory_id)

        # Observatorium fixieren
        selected_id = str(selected_observatory_id)
        for x in form.head.observatory_name.choices:
            if x[0] == selected_id:
                form.head.observatory_name.choices = [(x[0], x[1])]
                break

        # Poweruser choices
        selected_poweruser_id = str(order_head.request_poweruser_id)
        form.head.poweruser_name.choices = [("", "Auswählen oder leer lassen")] + [
            (str(x.id), x.display_name()) for x in poweruser_query()
        ]
        if selected_poweruser_id:
            form.head.poweruser_name.data = selected_poweruser_id

        return render_template(
            "edit_order_pos.html",
            expert_mode=expert_mode,
            form=form,
            order_id=order_id,
            blocks=blocks,
        )

    # -------------------------
    # POST: Formular lesen
    # -------------------------
    form = ObservationRequestPositionsForm(request.form)

    # -------------------------
    # POST save_order or submit-order: Kopf + Positionen speichern (inkl. block_no / row_in_block)
    # -------------------------
    if action == "save_order" or action == "submit_order":
        # Kopf speichern
        apply_head(order_head, form.head)
        order_head.name = form.head.requester_name.data
        requested_date = order_head.request_date  # still readable after a rollback
        reservation, message = prepare_reservation_service(order_head)
        if reservation is None:
            db.session.rollback()
            flash(message, "warning")
            return redirect(url_for("orders.edit_order_pos", order_id=order_id))
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            reference = error_reference()
            current_app.logger.exception(
                "[%s] Reservierung für Antrag %s konnte nicht gespeichert werden", reference, order_id)
            flash(reservation_error_message(exc, requested_date, reference), "danger")
            return redirect(url_for("orders.edit_order_pos", order_id=order_id))

        try:
            save_positions_service(form, order_id, request.form)
            db.session.commit()
            flash("Deine Eingaben sind gespeichert!", "success")
            if action == "save_order":
                return redirect (url_for("orders.edit_order_pos", order_id=order_id))
            # kein 'return' wenn "submit_order"

        except Exception:
            db.session.rollback()
            reference = error_reference()
            current_app.logger.exception("[%s] Antrag %s konnte nicht gespeichert werden", reference, order_id)
            flash(save_failed_message("Der Antrag", reference), "danger")
            return redirect(url_for("orders.edit_order_pos", order_id=order_id))

    # -------------------------
    # resolve_coordinates
    # -------------------------
    if action == "resolve_coordinates":
        form.positions, count, resolved, ambigious = resolve_coordinates_service(form.positions)
        flash(
            f"Von {count} Objekten wurden bei {resolved} Koordinaten zugeordnet. {ambigious} ohne Zuordnung.",
            "success",
        )

        set_position_choices(form, selected_observatory_id)

        selected_id = str(selected_observatory_id)
        for x in form.head.observatory_name.choices:
            if x[0] == selected_id:
                form.head.observatory_name.choices = [(selected_id, x[1])]
                break

        # blocks für resolve_coordinates-Render (wie im GET)
        blocks = []
        current_block_no = None
        current_block = None
        for global_idx in range(len(form.positions)):
            # wenn resolve_coordinates_service block_no nicht kennt, legen wir alles in einen Block
            # (im normalen Save/Reload kommt es aus DB korrekt)
            bno = 1
            if current_block_no != bno:
                current_block_no = bno
                current_block = {"block_no": bno, "row_indices": []}
                blocks.append(current_block)
            current_block["row_indices"].append(global_idx)

        return render_template(
            "edit_order_pos.html",
            expert_mode=expert_mode,
            form=form,
            order_id=order_id,
            blocks=blocks,
        )

    # -------------------------
    # submit_order
    # -------------------------
    if action == "submit_order":
        for message, category in submit_order_service(order_id):
            flash(message, category)
        return redirect(url_for("orders.show_orders"))

    return redirect(url_for("orders.show_orders"))
