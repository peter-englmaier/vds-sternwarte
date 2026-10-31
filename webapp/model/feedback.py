from datetime import datetime, timezone

from webapp import db

class ObservationFeedbackPosition(db.Model):
    __tablename__ = 'beobachtungsrueckmeldung_position'

    id = db.Column(db.Integer, primary_key=True)

    feedback_id = db.Column(
        db.Integer,
        db.ForeignKey('beobachtungsrueckmeldung.id'),
        nullable=False,
        index=True,
    )

    source_position_id = db.Column(
        db.Integer,
        db.ForeignKey('observation_request_position.id'),
    )

    observation_request_id = db.Column(
        db.Integer,
        db.ForeignKey('observation_request.id'),
        nullable=False,
    )

    row_no = db.Column(db.Integer, nullable=False)

    telescope_id = db.Column(
        db.Integer,
        db.ForeignKey('telescope.id'),
        nullable=False,
    )

    filterset_id = db.Column(
        db.Integer,
        db.ForeignKey('filterset.id'),
    )

    target_objecttype = db.Column(db.String(200))
    target = db.Column(db.String(200))
    target_coordinates = db.Column(db.String(200))
    target_coordinates_lock = db.Column(db.String(1))

    exposure_count = db.Column(db.Integer)
    exposure_time = db.Column(db.Integer)
    mosaic = db.Column(db.Boolean, nullable=False, default=False)

    exposure_gain = db.Column(db.Integer)
    exposure_offset = db.Column(db.Integer)
    exposure_dither = db.Column(db.Integer)
    exposure_focus = db.Column(db.Integer)
    exposure_starttime = db.Column(db.Time)

    ra_h = db.Column(db.Integer)
    ra_m = db.Column(db.Integer)
    ra_s = db.Column(db.Float)

    dec_sign = db.Column(db.String(1))
    dec_d = db.Column(db.Integer)
    dec_m = db.Column(db.Integer)
    dec_s = db.Column(db.Float)

    block_no = db.Column(db.Integer, nullable=False)
    row_in_block = db.Column(db.Integer, nullable=False)

class ObservationFeedback(db.Model):
    __tablename__ = 'beobachtungsrueckmeldung'

    id = db.Column(db.Integer, primary_key=True)

    source_request_id = db.Column(
        db.Integer,
        db.ForeignKey('observation_request.id'),
        nullable=False,
        unique=True,
    )

    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
    )

    date_created = db.Column(db.DateTime, nullable=False)
    request_date = db.Column(db.DateTime, nullable=False)

    request_observatory_id = db.Column(
        db.Integer,
        db.ForeignKey('observatory.id'),
        nullable=False,
    )

    request_type = db.Column(db.String(10), nullable=False)

    request_poweruser_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
    )

    remark = db.Column(db.String(2000))

    status = db.Column(
        db.String(10),
        nullable=False,
        default='14',
        index=True,
    )

    copied_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    completed_at = db.Column(db.DateTime(timezone=True))

    completed_by_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
    )

    matches_request = db.Column(db.Boolean)
    deviations = db.Column(db.String(2000))

    positions = db.relationship(
        'ObservationFeedbackPosition',
        backref='feedback',
        cascade='all, delete-orphan',
        order_by='ObservationFeedbackPosition.row_no',
    )

    observatory_name = db.relationship('Observatory')

    poweruser = db.relationship(
        'User',
        foreign_keys=[request_poweruser_id],
    )