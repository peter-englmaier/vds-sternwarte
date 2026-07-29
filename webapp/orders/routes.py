from smtplib import SMTPAuthenticationError

from flask import (
    render_template,
    url_for,
    flash,
    redirect,
    request,
    abort,
    jsonify,
)
from flask_login import current_user, login_required
from flask import current_app
from flask_mail import Message
from datetime import date, datetime
from celery import shared_task
from sqlalchemy import true

from webapp import db, mail, Config
from webapp.errors.handlers import *
from webapp.model.db import User, Group, ObservationRequest, ObservationRequestPosition, ObservatoryReservation, Observatory

from webapp.orders import orders  # Blueprint-Objekt
from webapp.orders.orderform import (
    ObservationRequestPositionsForm,
    ObservationRequestHead,
    RejectOrderForm,
    telescope_query,
    filterset_query,
    poweruser_query,
)
from webapp.orders.constants import (
    ORDER_STATUS_LABELS,
    ORDER_STATUS_CREATED,
    ORDER_STATUS_WAITING,
    ORDER_STATUS_PU_ACCEPTED,
    ORDER_STATUS_REJECTED,
    USER_ROLE_ADMIN,
    ORDER_STATUS_APPROVED,
    ORDER_STATUS_PU_ASSIGNED,
)
from webapp.orders.orderservices import (
    copy_order_service,
    delete_order_service,
    calendar_service,
    resolve_coordinates_service,
    init_new_order_service,
    init_new_orderpos_service,
    set_user_preference_service,
    get_user_preference_service,
)
from webapp.users.utils import role_required


# ------------------------------------------------------------------
# User preference laden
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["GET"])
@login_required
def get_user_preference():
    key = request.args.get("key")
    value = get_user_preference_service(current_user.id, key, False)
    return jsonify(success=True, value=value)


# ------------------------------------------------------------------
# User preference speichern
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["POST"])
@login_required
def set_user_preference():
    data = request.get_json()
    key = data.get("key")
    value = data.get("value")
    default = data.get("default")  # falls benötigt

    status, message = set_user_preference_service(current_user.id, key, value, default)

    if status == 1:
        # Fehlerfall
        print(f"ERROR: {message}")
        return jsonify(success=False, error="Ein fehler ist aufgetreten; siehe logfile."), 500
    else:
    # Erfolg
        return jsonify(success=True)


# --------------------------------------------------------------
# Teleskope zum Observatorium
# --------------------------------------------------------------
@orders.route('/orders/get_telescopes/<int:observatory_id>')
def get_telescopes():
    data = request.get_json()
    observatory_id = data.get('observatory_id')
    telescopes = telescope_query(observatory_id)
    return jsonify([{'id': t.id, 'name': t.name} for t in telescopes])


# --------------------------------------------------------------
# Filtersets zum Teleskop
# --------------------------------------------------------------
@orders.route("/orders/get_filtersets", methods=["POST"])
@login_required
def get_filtersets():
    data = request.get_json()
    telescope_id = data.get("telescope_id")
    filtersets = filterset_query(telescope_id)
    return jsonify([{"id": f.id, "name": f.name} for f in filtersets])


# --------------------------------------------------------------------
# Beobachtungsantrag bearbeiten
# --------------------------------------------------------------------
@orders.route("/orders", methods=["GET"])
@login_required
@role_required("user")
def show_orders():
    user_orders = ObservationRequest.query.filter_by(user_id=current_user.id).all()
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
    order = ObservationRequest.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    if order.status not in {ORDER_STATUS_CREATED, ORDER_STATUS_REJECTED}:
        abort(403)

    rc, message = delete_order_service(order_id)
    flash(message, "success" if rc == 0 else "danger")
    return redirect("/orders")


# --------------------------------------------------------------------
# Beobachtungsantrag erstellen, abschicken, sichern oder anzeigen
# --------------------------------------------------------------------
@orders.route("/actionhandler", methods=["POST"])
@login_required
@role_required("user")
def actionhandler():
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
            order_head.name = form.requester_name.data
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
    action = request.form.get("action")

    order_head = ObservationRequest.query.get(order_id)
    if order_head is None:
        abort(403)
    if order_head.user_id != current_user.id and not current_user.has_role(USER_ROLE_ADMIN):
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


# --------------------------------------------------------------------
# Beobachtungsantrag mit allen Positionen anzeigen
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/positions", methods=["GET"])
@login_required
def show_order_positions(order_id):
    user_order = ObservationRequest.query.get(order_id)
    if not user_order:
        return error_404("Order does not exist")
    user_order.status_label = ORDER_STATUS_LABELS.get(user_order.status, "??")
    user = User.query.get(user_order.user_id)
    pu_user = User.query.get(user_order.request_poweruser_id)
    positions = ObservationRequestPosition.query.filter_by(observation_request_id=order_id).all()
    observatory = Observatory.query.get(user_order.request_observatory_id)
    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    return render_template("order_positions.html", order=user_order, order_position=positions,
                           user=user, pu_user=pu_user, observatory=observatory, reservation=reservation)


# --------------------------------------------------------------------
# Poweruser weist sich Antrag zu
# --------------------------------------------------------------------
@orders.route("/poweruser/<int:order_id>/pu_accept", methods=["POST"])
@login_required
@role_required("poweruser")
def pu_accept(order_id):
    order_head = ObservationRequest.query.get(order_id)
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
# Der Kontrolleur (Approver) weist Antrag zurück
# --------------------------------------------------------------------
@orders.route("/approver/<int:order_id>/reject", methods=["GET", "POST"])
@login_required
@role_required("approver")
def reject_order(order_id):
    order_head = ObservationRequest.query.get_or_404(order_id)
    user=User.query.get(order_head.user_id)
    observatory = Observatory.query.get(order_head.request_observatory_id)
    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    order_head.status_label = ORDER_STATUS_LABELS.get(order_head.status, "??")
    form = RejectOrderForm()
    if form.validate_on_submit():
        if form.data['submit']:
            done=False
            try:
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
                           form=form, order=order_head, user=user, observatory=observatory, reservation=reservation)


# --------------------------------------------------------------------
# Der Kontrolleur (Approver) akzeptiert Antrag
# --------------------------------------------------------------------
@orders.route("/approver/<int:order_id>/approve", methods=["POST"])
@login_required
@role_required("approver")
def approve_order(order_id):
    order_head = ObservationRequest.query.get(order_id)
    order_head.status = ORDER_STATUS_APPROVED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(
            f"Es ist ein Fehler aufgetreten: {e}. Bitte melden Sie sich beim Systemadministrator.",
            "danger",
        )
    else:
        flash("Antrag bestätigt", "success")
    return redirect(url_for("main.approver"))

@orders.route("/approver/assign_poweruser_form", methods=["GET"])
@login_required
@role_required("approver")
def approver_assign_poweruser_form():
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

@shared_task
def send_approve_email(order_id, approver_id, order_url, info):
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)
    pu = User.query.get(antrag.request_poweruser_id)
    request_date = antrag.request_date.strftime('%d.%m.%Y')

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()
    pu_greeting = pu.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."

    recipients = [user.email, approver.email, pu.email]

    msg = Message('Antrag genehmigt',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},
    
die beantragte Beobachtung #{order_id} für den {request_date} wurde genehmigt.
Der Termin ist im Kalender entsprechend reserviert.

Deine Beobachtung wird betreut durch: PU {pu_greeting}
Link zum Antrag: {order_url}
{info or ""}
Wie geht es nun weiter?
- PU {pu_greeting} wird Dich kontaktieren. Für die Kommunikation setzen JITSI https://jitsi.decoit.de/VdS-Sternwarte ein. Dieses ist eine rein Webbrowser basiertende Anwendung und bedarf keiner weiteren Installation.
- Bitte bereite dich auf die Beobachtung  in dem Sinne vor, das alle Informationen zur Erstellung einer N.I.N.A Sequenz durch den PU möglich ist.
- Informiere dich über das Wetter vor Ort. Es ist nicht ausgeschlossen, das die Beobachtung aufgrund von instabilen Bedingungen nicht möglich ist.
- Wir erstellen eine Statistik über die beobachteten Objekte – auch um Mehrfachbeobachtungen zu minimieren. Daher trage bitte die durchgeführten Belichtungen hier ein: https://nextcloud.sternfreunde.de/index.php/f/104569.

Bitte berücksichtige auch potenzielle allgemeine Bekanntmachungen.

Danke für die Beachtung und viel Erfolg.

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc



@shared_task
def send_reject_email(order_id, approver_id, order_url, info):
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."

    recipients = [user.email, approver.email]

    msg = Message('Antrag abgelehnt',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},

Dein Antrag mit der Nummer #{order_id} wurde leider abgelehnt. Gegebenenfalls ist unten eine Erläuterung zu finden.

Link zum Antrag: {order_url}

Erläuterung: {info or "keine"}

Wie geht es nun weiter?
- Falls eine Erläuterung vorhanden ist, bitte diese in einem neuen Antrag berücksichtigen.
- Gegebenenfalls Kontaktaufnahme via Email.

Sorry, Danke!

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc



# --------------------------------------------------------------------
# Belegungskalender anzeigen
# --------------------------------------------------------------------
@orders.route("/orders/show_calendar", methods=["GET"])
@login_required
@role_required("user")
def show_calendar():
    year = request.args.get("year", default=datetime.now().year, type=int)
    month = request.args.get("month", default=datetime.now().month, type=int)
    picker = request.args.get("picker", default=False, type=bool)
    target_id = request.args.get("target_id", default="request_date", type=str)
    display_id = request.args.get("display_id", default="selected_date_display", type=str)

    (cal, planned_days, approved_days,
     new_moon_days, phase1_moon_days, phase2_moon_days, phase3_moon_days,
     full_moon_days, phase5_moon_days, phase6_moon_days, phase7_moon_days) = calendar_service(year, month)
    today = date.today()
    referrer = request.referrer

    template = "_calendar.html" if request.headers.get("HX-Request") else "calendar.html"
    month_name = [ "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember" ]
    return render_template(
        template,
        datetime=datetime,
        cal=cal,
        planned_days=planned_days,
        approved_days=approved_days,
        full_moon_days=full_moon_days,
        phase1_moon_days=phase1_moon_days,
        phase2_moon_days=phase2_moon_days,
        phase3_moon_days=phase3_moon_days,
        new_moon_days=new_moon_days,
        phase5_moon_days=phase5_moon_days,
        phase6_moon_days=phase6_moon_days,
        phase7_moon_days=phase7_moon_days,
        month=month,
        year=year,
        today_day=today.day,
        today_month=today.month,
        today_year=today.year,
        referrer=referrer,
        picker=picker,
        target_id=target_id,
        display_id=display_id,
        month_name=month_name
    )

# --------------------------------------------------------------------
# Observation Requests Gesamt
# --------------------------------------------------------------------

@orders.route("/obs_requests")
@login_required
def obs_request_complete():
    orders = ObservationRequest.query.order_by(ObservationRequest.id.desc()).all()

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
