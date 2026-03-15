# create reservations for existing observation requests

from webapp import create_app, db
from webapp.model.db import Observatory, ObservationRequest, ObservatoryReservation

app=create_app()

def upgrade():
    with app.app_context():
        requests = ObservationRequest.query.all()
        for request in requests:
            observatory = Observatory.query.get(request.request_observatory_id)
            reservation = ObservatoryReservation(date=request.request_date, observatory=observatory,
                                                 request=request)
            try:
                db.session.add(reservation)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f'Cannot create {reservation} because {e}')
