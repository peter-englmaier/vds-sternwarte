"""Poweruser page: open orders, own and other assigned orders, feedback on availability.

Routes::

    GET   /poweruser  poweruser()  -> poweruser.html
    POST  /poweruser  poweruser()  -> HTML fragment (HTMX), action "pu_meldung"
"""
from datetime import date, timedelta

from flask import render_template, request
from flask_login import current_user, login_required
from markupsafe import escape
from sqlalchemy import select

from webapp.main import main  # blueprint object
from webapp.model.db import db, ObservationRequest, PoweruserMeldung, User
from webapp.orders.constants import ORDER_STATUS_LABELS, ORDER_STATUS_PU_REJECTED, ORDER_STATUS_APPROVED, \
    ORDER_STATUS_PU_ASSIGNED
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Poweruser-Seite anzeigen und Rückmeldung speichern
# --------------------------------------------------------------------
@main.route("/poweruser", methods=['GET','POST'])
@login_required
@role_required("poweruser")
def poweruser():
    """Show the poweruser page (GET) or save the availability feedback of
    the current poweruser for an order (POST, HTMX).

    GET lists:

    * open orders (status approved) with the user's own feedback,
    * orders assigned to the current user,
    * orders assigned to other powerusers.

    Assigned orders older than three days are hidden.

    POST expects the form fields ``action`` (must be ``"pu_meldung"``),
    ``order_id`` and ``availability``:

    * 1, 2: available, 3: not available, 4: withdraw feedback.
    * If the order is assigned to the current user and they answer 3, the
      order goes to status PU rejected.

    The response replaces ``#pu-feedback-<order_id>`` and updates
    ``#pu-count-<order_id>`` out of band with the number of positive feedbacks.

    :return: rendered ``poweruser.html`` (GET), or an HTML fragment (POST);
        status 400 for an unknown action or invalid input.
    :raises NotFound: if the order does not exist (POST).
    """

    if request.method == "POST":
        action = request.form.get("action")
        if action != "pu_meldung":
            return '<span id="pu-feedback-0" class="text-danger ms-2">Unbekannte Aktion</span>', 400

        order_id = request.form.get("order_id", type=int)
        availability = request.form.get("availability", type=int)

        order_id_html = escape(str(order_id or 0))

        if not order_id or availability not in (1, 2, 3, 4):
            return (
                f'<span id="pu-feedback-{order_id_html}" class="text-danger ms-2">Ungültige Eingabe</span>',
                400,
            )

        order = ObservationRequest.query.get_or_404(order_id)

        is_assigned_to_current_user = (
        order.status == ORDER_STATUS_PU_ASSIGNED
        and order.request_poweruser_id == current_user.id
        )

        meldung = PoweruserMeldung.query.filter_by(
            observation_request_id=order_id,
            poweruser_user_id=current_user.id
        ).first()

                # 4 = Keine Rückmeldung
        if availability == 4:
            if meldung is not None:
                db.session.delete(meldung)

            db.session.commit()

            positive_feedback_count = PoweruserMeldung.query.filter(
                PoweruserMeldung.observation_request_id == order_id,
                PoweruserMeldung.availability.in_([1, 2])
            ).count()

            if positive_feedback_count == 1:
                count_text = "Es hat bereits 1 PU zurückgemeldet."
            elif positive_feedback_count > 1:
                count_text = f"Es haben bereits {positive_feedback_count} PUs zurückgemeldet."
            else:
                count_text = ""

            return (
                f'<span id="pu-feedback-{order_id_html}">'
                f'<div class="mt-1">'
                f'<span class="text-muted">'
                f'Keine Rückmeldung eingereicht'
                f'</span>'
                f'</div>'
                f'</span>'
                f'<div id="pu-count-{order_id_html}" '
                f'class="text-muted mt-1" '
                f'hx-swap-oob="innerHTML">'
                f'{count_text}'
                f'</div>'
            )

        if meldung is None:
            meldung = PoweruserMeldung(
                observation_request_id=order_id,
                poweruser_user_id=current_user.id,
                availability=availability
            )
            db.session.add(meldung)
        else:
            meldung.availability = availability

# Bereits zugewiesener Poweruser kann den Termin doch nicht wahrnehmen
        if is_assigned_to_current_user and availability == 3:
            order.status = ORDER_STATUS_PU_REJECTED

        db.session.commit()

        positive_feedback_count = PoweruserMeldung.query.filter(
            PoweruserMeldung.observation_request_id == order_id,
            PoweruserMeldung.availability.in_([1, 2])
        ).count()

        if positive_feedback_count == 1:
            count_text = "Es hat bereits 1 PU zurückgemeldet."
        elif positive_feedback_count > 1:
            count_text = f"Es haben bereits {positive_feedback_count} PUs zurückgemeldet."
        else:
            count_text = ""

        return (
    f'<span id="pu-feedback-{order_id_html}">'
    f'<div class="mt-1">'
    f'<span class="text-success">'
    f'Rückmeldung ist eingereicht'
    f'</span>'
    f'<br>'
    f'<small class="text-muted">'
    f'Die Antwort kann bis zur Zuweisung durch den Approver geändert werden:'
    f'</small>'
    f'</div>'
    f'</span>'
    f'<div id="pu-count-{order_id_html}" '
    f'class="text-muted mt-1" '
    f'hx-swap-oob="innerHTML">'
    f'{count_text}'
    f'</div>'
        )

    # GET
    cutoff_date = date.today() - timedelta(days=3)
    stmt = (
        select(ObservationRequest, User)
        .outerjoin(
            User,
            User.id == ObservationRequest.request_poweruser_id,
        )
        .where(
            ObservationRequest.status.in_([
                ORDER_STATUS_APPROVED,
                ORDER_STATUS_PU_ASSIGNED,
            ])
        )
        .order_by(
            ObservationRequest.request_date.desc(),
            ObservationRequest.id.desc(),
        )
    )
    all_rows = db.session.execute(stmt).unique().all()

    open_orders = []
    own_orders = []
    others_orders = []

    my_meldungen_by_order = {
        meldung.observation_request_id: meldung.availability
        for meldung in PoweruserMeldung.query.filter_by(
            poweruser_user_id=current_user.id
        ).all()
    }

    for order, pu_user in all_rows:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")

        order.positive_feedback_count = PoweruserMeldung.query.filter(
            PoweruserMeldung.observation_request_id == order.id,
            PoweruserMeldung.availability.in_([1, 2])
        ).count()

        if order.status == ORDER_STATUS_APPROVED:
            # Noch nicht zugewiesene Anträge
            order.poweruser_name = (
                pu_user.display_name()
                if pu_user
                else None
            )
            order.my_pu_meldung_availability = my_meldungen_by_order.get(order.id)
            open_orders.append(order)

        elif order.status == ORDER_STATUS_PU_ASSIGNED:
            order.poweruser_name = (
                pu_user.display_name()
                if pu_user
                else None
            )

        if order.request_date.date() >= cutoff_date:
            if order.status == ORDER_STATUS_PU_ASSIGNED and order.request_poweruser_id == current_user.id:
                order.my_pu_meldung_availability = my_meldungen_by_order.get(order.id)
                own_orders.append(order)
            elif order.status == ORDER_STATUS_PU_ASSIGNED:
                others_orders.append(order)

    return render_template("poweruser.html",title="Poweruser",open_orders=open_orders,own_orders=own_orders,others_orders=others_orders,)
