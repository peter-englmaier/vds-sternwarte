from celery import shared_task
from webapp import db
from webapp.model.db import ObservatoryReservation

@shared_task
def expire_reservations_task():
    numExpired=0
    for reservation in ObservatoryReservation.query.all():
        if reservation.is_expired():
            numExpired = numExpired + 1
            db.session.delete(reservation)
            db.session.commit()
    return f"{numExpired} reservations expired"
