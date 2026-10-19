"""Edit an order and its positions.

Routes::

    GET, POST  /orders/<int:order_id>/edit  edit_order_pos()  -> edit_order_pos.html or redirect
"""
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import current_user, login_required

from webapp import db
from webapp.model.db import User, ObservationRequest, ObservationRequestPosition, ObservatoryReservation, Observatory
from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import (
    ObservationRequestPositionsForm,
    telescope_query,
    filterset_query,
    poweruser_query,
)
from webapp.orders.constants import (
    ORDER_STATUS_LABELS,
    ORDER_STATUS_CREATED,
    ORDER_STATUS_WAITING,
    ORDER_STATUS_REJECTED,
    USER_ROLE_ADMIN,
)
from webapp.orders.orderservices import (
    resolve_coordinates_service,
    init_new_orderpos_service,
    get_user_preference_service,
)


# --------------------------------------------------------------------
# Beobachtungsantrag bearbeiten, Zeilen hinzufügen oder entfernen
# Der Kopfsatz muss schon vorhanden sein.
# Positionen werden, wenn vorhanden aus der DB geladen.
# Wenn keine Position existiert, wird eine neue mit zum Observatoruim passende
# Parametern erstellt
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/edit", methods=["GET", "POST"])
@login_required
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
        (admins excepted) or is not in status created or rejected.
    """
    action = request.form.get("action")

    order_head = ObservationRequest.query.get(order_id)
    if order_head is None:
        abort(403)
    if order_head.user_id != current_user.id and not current_user.has_role(USER_ROLE_ADMIN):
        abort(403)
    if order_head.status not in {ORDER_STATUS_CREATED, ORDER_STATUS_REJECTED}:
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
            position_items = init_new_orderpos_service()

            telescope_id = telescope_query(selected_observatory_id)[0].id
            position_items[0].telescope_id = telescope_id

            fs = filterset_query(telescope_id)
            if fs:
                position_items[0].filterset_id = fs[0].id

            # Defaults
            try:
                position_items[0].block_no = 1
                position_items[0].row_in_block = 1
            except Exception:
                pass

        # -------------------------
        # blocks-Struktur für Template erzeugen
        # Template erwartet: blocks = [{ block_no: int, row_indices: [0..] }, ...]
        # row_indices bezieht sich auf die globale WTForms-Liste form.positions[]
        # -------------------------
        blocks = []
        current_block_no = None
        current_block = None

        position_data = []
        for pos in position_items:
            position_data.append(
                {
                    "telescope": pos.telescope_id,
                    "target": pos.target,
                    "filterset": pos.filterset_id,
                    "target_objecttype": pos.target_objecttype,
                    "target_coordinates": pos.target_coordinates,
                    "target_coordinates_lock": pos.target_coordinates_lock != "0",
                    "exposure_count": pos.exposure_count,
                    "exposure_time": pos.exposure_time,
                    "mosaic": bool(getattr(pos, "mosaic", False)),
                    "exposure_starttime": pos.exposure_starttime,
                    "exposure_gain": pos.exposure_gain,
                    "exposure_offset": pos.exposure_offset,
                    "exposure_dither": pos.exposure_dither,
                    "exposure_focus": pos.exposure_focus,
                }
            )

        form.process(
            data={
                "order_id": order_id,
                "head": head_data,
                "positions": position_data,
            }
        )

        # Jetzt, nachdem form.positions existiert: row_indices pro Block bauen
        for global_idx, pos in enumerate(position_items):
            bno = getattr(pos, "block_no", 1) or 1
            if current_block_no != bno:
                current_block_no = bno
                current_block = {"block_no": bno, "row_indices": []}
                blocks.append(current_block)
            current_block["row_indices"].append(global_idx)

        # Choices setzen
        for pos_form in form.positions:
            selected_telescope_id = pos_form.telescope.data
            selected_filterset_id = pos_form.filterset.data

            tel_choices = telescope_query(selected_observatory_id)
            pos_form.telescope.choices = [(x.id, x.name) for x in tel_choices]

            fs_choices = filterset_query(selected_telescope_id)
            if not selected_filterset_id:
                pos_form.filterset.choices = [("", "Auswählen")] + [(x.id, x.name) for x in fs_choices]
            else:
                pos_form.filterset.choices = [(x.id, x.name) for x in fs_choices]

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
        order_head.request_date = form.head.request_date.data
        order_head.request_observatory_id = form.head.observatory_name.data
        observatory = Observatory.query.get(order_head.request_observatory_id)
        reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first();
        if not reservation:
            reservation = ObservatoryReservation(order_head.request_date,observatory,order_head)
        else:
            reservation.set_observatory(observatory).set_date(order_head.request_date)
        try:
            db.session.add(reservation)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Reservation nicht möglich", "danger")
            return redirect(url_for("orders.edit_order_pos", order_id=order_id))

        order_head.name = form.head.requester_name.data
        #order_head.request_purpose = form.head.request_purpose.data
        poweruser_index = form.head.poweruser_name.data
        if poweruser_index != '':
            poweruser = next((name for i, name in form.head.poweruser_name.choices if i == poweruser_index), None)
            # poweruser now holds the display_name, not the name of the power user
            pw_users = User.by_role('poweruser')
            for pwuser in pw_users:
                if pwuser.display_name() == poweruser:
                    order_head.request_poweruser_id = pwuser.id
                    break
        order_head.request_type = form.head.request_type.data
        order_head.remark = form.head.remark.data

        try:
            ObservationRequestPosition.query.filter_by(observation_request_id=order_id).delete()

            for idx, pos_form in enumerate(form.positions):
                # Wichtig: block_no und row_in_block kommen NICHT aus WTForms-Feldern,
                # sondern aus den hidden Inputs, die dein Flattening erzeugt.
                block_no_raw = request.form.get(f"positions-{idx}-block_no", "1")
                row_in_block_raw = request.form.get(f"positions-{idx}-row_in_block", "1")

                try:
                    block_no = int(block_no_raw)
                except Exception:
                    block_no = 1

                try:
                    row_in_block = int(row_in_block_raw)
                except Exception:
                    row_in_block = 1

                # target_coordinates_lock: DB ist VARCHAR(1)
                # -> konsistent als "0"/"1" speichern, damit GET ( != "0") stimmt
                lock_val = pos_form.target_coordinates_lock.data
                if isinstance(lock_val, str):
                    # falls schon "0"/"1" geliefert wird
                    lock_db = lock_val
                else:
                    lock_db = "1" if lock_val else "0"

                db.session.add(
                    ObservationRequestPosition(
                        row_no=idx + 1,
                        block_no=block_no,
                        row_in_block=row_in_block,
                        observation_request_id=order_id,
                        telescope_id=pos_form.telescope.data,
                        target=pos_form.target.data,
                        filterset_id=pos_form.filterset.data,
                        target_objecttype=pos_form.target_objecttype.data,
                        target_coordinates=pos_form.target_coordinates.data,
                        target_coordinates_lock=lock_db,
                        exposure_count=pos_form.exposure_count.data,
                        exposure_time=pos_form.exposure_time.data,
                        mosaic=bool(pos_form.mosaic.data),
                        exposure_starttime=pos_form.exposure_starttime.data,
                        exposure_gain=pos_form.exposure_gain.data,
                        exposure_offset=pos_form.exposure_offset.data,
                        exposure_dither=pos_form.exposure_dither.data,
                        exposure_focus=pos_form.exposure_focus.data,
                    )
                )

            db.session.commit()
            flash("Deine Eingaben sind gespeichert!", "success")
            #return redirect(url_for("orders.edit_order_pos", order_id=order_id))
            if action == "save_order":
                return redirect (url_for("orders.edit_order_pos", order_id=order_id))
            # kein 'return' wenn "save_order"

        except Exception as e:
            db.session.rollback()
            flash(f"Es ist ein Fehler aufgetreten: {e}", "danger")
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

        for pos_form in form.positions:
            selected_telescope_id = pos_form.telescope.data
            selected_filterset_id = pos_form.filterset.data

            tel_choices = telescope_query(selected_observatory_id)
            pos_form.telescope.choices = [(x.id, x.name) for x in tel_choices]

            fs_choices = filterset_query(selected_telescope_id)
            if not selected_filterset_id:
                pos_form.filterset.choices = [("", "Auswählen")] + [(x.id, x.name) for x in fs_choices]
            else:
                pos_form.filterset.choices = [(x.id, x.name) for x in fs_choices]

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
        order_head = ObservationRequest.query.get(order_id)
        order_head.status = ORDER_STATUS_WAITING
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(
                f"Es ist ein Fehler aufgetreten: {e}. Bitte melden Sie sich beim Systemadministrator.",
                "danger",
            )
        # freeze reservation
        reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first();
        if reservation:
            try:
                reservation.freeze()
                db.session.add(reservation)
                db.session.commit()
            except Exception as e:
                print(f"Es ist ein Fehler aufgetreten: {e}.")
                db.session.rollback()
                flash(
                    f"Die reservation ist bereits abgelaufen und kann nicht mehr aufrechterhalten werden",
                    "warning"
                )

        return redirect("/orders")

    return redirect("/orders")
