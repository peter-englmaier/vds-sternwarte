# create reservations for existing observation requests

from webapp import create_app, db
from webapp.model.db import Observatory, ObservationRequest, ObservatoryReservation
from webapp.orders.constants import ORDER_STATUS_PU_ASSIGNED

app=create_app()

def upgrade():
    with app.app_context():
        requests = ObservationRequest.query.all()
        for request in requests:
            observatory = Observatory.query.get(request.request_observatory_id)
            reservation = ObservatoryReservation(date=request.request_date, observatory=observatory,
                                                 request=request)
            if request.status == ORDER_STATUS_PU_ASSIGNED:
                reservation.confirm()
            print(f'Create {reservation.date}')
            try:
                db.session.add(reservation)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f'Cannot create reservation because {e}')
