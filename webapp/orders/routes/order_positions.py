"""Show an order with all positions and download it as iCalendar.

Routes::

    GET  /orders/<int:order_id>/positions        show_order_positions()       -> order_positions.html
    GET  /orders/<int:order_id>/reservation.ics  download_reservation_ical()  -> iCalendar file (.ics)
"""
from datetime import datetime, timedelta
from datetime import timezone

from flask import render_template, abort, Response
from flask_login import login_required
from icalendar import Calendar, Event

from webapp.errors.handlers import error_404
from webapp.model.db import User, ObservationRequest, ObservationRequestPosition, ObservatoryReservation, Observatory
from webapp.orders import orders  # blueprint object
from webapp.orders.constants import ORDER_STATUS_LABELS


# --------------------------------------------------------------------
# Beobachtungsantrag mit allen Positionen anzeigen
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/positions", methods=["GET"])
@login_required
def show_order_positions(order_id):
    """Show an order with all its positions, users, observatory and reservation.

    :param order_id: id of the order.
    :return: rendered ``order_positions.html``, or the 404 page if the order
        does not exist.
    """
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
# iCalendar-Download für Anträge
# --------------------------------------------------------------------
@orders.route("/orders/<int:order_id>/reservation.ics", methods=["GET"])
@login_required
def download_reservation_ical(order_id):
    """Download the reservation of an order as iCalendar file.

    The all-day event gets the status ``CONFIRMED`` for a booked reservation,
    ``CANCELLED`` for an expired one and ``TENTATIVE`` otherwise.

    :param order_id: id of the order.
    :return: ``text/calendar`` response as attachment ``reservierung-<order_id>.ics``.
    :raises NotFound: if the order or its reservation does not exist.
    """
    order = ObservationRequest.query.get_or_404(order_id)
    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    # Which other options are to be expected?
    # However, let's be conservative.
    if not reservation:
        abort(404)

    positions = ObservationRequestPosition.query.filter_by(observation_request_id=order_id).all()
    targets = list(dict.fromkeys(
        position.target.strip()
        for position in positions
        if position.target and position.target.strip()
    ))
    observatory = Observatory.query.get(order.request_observatory_id)
    reservation_date = reservation.date.date() if isinstance(reservation.date, datetime) else reservation.date

    calendar = Calendar()
    calendar.add("prodid", "-//VdS Sternwarte//Observatory Reservation//DE")
    calendar.add("version", "2.0")

    event = Event()
    event.add("uid", f"reservation-{reservation.id}@vds-sternwarte")
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("dtstart", reservation_date)
    event.add("dtend", reservation_date + timedelta(days=1))
    event.add("summary", f"Sternwartenreservierung: {observatory.name if observatory else 'Observatorium'}")
    event.add("description", "\n".join((
        f"Antrag zum {order.request_date.strftime('%d.%m.%Y')}",
        f"Antragsstatus: {ORDER_STATUS_LABELS.get(order.status, 'Unbekannt')}",
        f"Reservierungsstatus: {reservation}",
        f"Objekt(e): {', '.join(targets) if targets else 'Kein Objekt angegeben'}",
    )))
    if observatory:
        location = observatory.name
        if observatory.site:
            location = f"{location}, {observatory.site.name}"
        event.add("location", location)

    if reservation.status == ObservatoryReservation.Status.BOOKED.name:
        event.add("status", "CONFIRMED")
    elif reservation.status == ObservatoryReservation.Status.EXPIRED.name:
        event.add("status", "CANCELLED")
    else:
        event.add("status", "TENTATIVE")
    calendar.add_component(event)

    return Response(
        calendar.to_ical(),
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=reservierung-{order_id}.ics"},
    )
