from datetime import date

from sqlalchemy.exc import IntegrityError

from webapp import db
from webapp.model.db import (
    ObservationRequest,
    ObservationRequestPosition,
)
from webapp.model.feedback import (
    ObservationFeedback,
    ObservationFeedbackPosition,
)
from webapp.orders.constants import (
    ORDER_STATUS_PU_ASSIGNED,
    ORDER_STATUS_PU_ACCEPTED,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_EXECUTED,
    ORDER_STATUS_PICURES_READY,
    ORDER_STATUS_STATISTICS_OPEN,
)

# Geeignete vergangene Anträge werden in die Beobachtungsrückmeldung übernommen.
# Abarbeitung der Anträge

HEAD_COLUMNS = tuple(
    column.name
    for column in ObservationRequest.__table__.columns
    if column.name not in ('id', 'status')
)

POSITION_COLUMNS = tuple(
    column.name
    for column in ObservationRequestPosition.__table__.columns
    if column.name != 'id'
)


def copy_due_feedback(user_id=None):
    query = ObservationRequest.query.filter(
        ObservationRequest.request_date < date.today(),

        ObservationRequest.request_type.in_(
            ('B', 'F', 'S', 'G')
        ),

        ObservationRequest.status.in_([
            ORDER_STATUS_PU_ASSIGNED,
            ORDER_STATUS_PU_ACCEPTED,
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_EXECUTED,
            ORDER_STATUS_PICURES_READY,
        ]),

        ~db.session.query(ObservationFeedback.id)
        .filter(
            ObservationFeedback.source_request_id
            == ObservationRequest.id
        )
        .exists(),
    )

    if user_id is not None:
        query = query.filter(
            ObservationRequest.user_id == user_id
        )

    copied = 0

    for order in query.order_by(ObservationRequest.id).all():
        try:
            with db.session.begin_nested():
                feedback = ObservationFeedback(
                    source_request_id=order.id,
                    status=ORDER_STATUS_STATISTICS_OPEN,
                    **{
                        name: getattr(order, name)
                        for name in HEAD_COLUMNS
                    },
                )

                for position in order.positions:
                    feedback.positions.append(
                        ObservationFeedbackPosition(
                            source_position_id=position.id,
                            **{
                                name: getattr(position, name)
                                for name in POSITION_COLUMNS
                            },
                        )
                    )

                db.session.add(feedback)
                db.session.flush()

            copied += 1

        except IntegrityError:
            existing = ObservationFeedback.query.filter_by(
                source_request_id=order.id
            ).first()

            if existing is None:
                raise

    db.session.commit()
    return copied