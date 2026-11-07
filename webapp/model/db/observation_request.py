from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from webapp import db


# ---------------------------------------------------------------
# ObservationRequest Kopfsatz
# ---------------------------------------------------------------
class ObservationRequest(db.Model):
    __tablename__ = 'observation_request'
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    request_date: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    request_observatory_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('observatory.id'), nullable=False)
    request_type: Mapped[str] = mapped_column(db.String(10), unique=False, nullable=False)  # Beobachtung, Führung, Wartung ...
    #request_purpose: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)  # Pritty pictures, Wissenschaft, Forschung ...
    request_poweruser_id: Mapped[str] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    remark: Mapped[str] = mapped_column(db.String(2000), nullable=True)
    status: Mapped[str] = mapped_column(db.String(10), nullable=False, default='0')
    positions = relationship(
        'ObservationRequestPosition',
        backref='observationrequest',
        cascade="all, delete-orphan",
        lazy='joined'
    )
    observatory_name = relationship('Observatory', backref='observation_request')

# ---------------------------------------------------------------
#  observationRequestPosition zum Kopfsatz gehörende Positionen
# ---------------------------------------------------------------
class ObservationRequestPosition(db.Model):
    __tablename__ = 'observation_request_position'
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    observation_request_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('observation_request.id'), nullable=False)
    row_no: Mapped[int] = mapped_column(db.Integer, nullable=False)
    telescope_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('telescope.id'), nullable=False)
    filterset_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('filterset.id'), nullable=True)
    target_objecttype: Mapped[str] = mapped_column(db.String(200), unique=False, nullable=True)
    target: Mapped[str] = mapped_column(db.String(200), unique=False, nullable=True)
    target_coordinates: Mapped[str] = mapped_column(db.String(200), unique=False, nullable=True)
    target_coordinates_lock: Mapped[str] = mapped_column(db.String(1), unique=False, nullable=True, default='0')
    exposure_count: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True)
    exposure_time: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True)
    mosaic: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    exposure_gain: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True, default='0')
    exposure_offset: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True, default='0')
    exposure_dither: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True, default='1')
    exposure_focus: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True, default='1')
    exposure_starttime = mapped_column(Time, nullable=True)

    # --- Koordinaten-Spalten (existieren in SQLite) ---
    ra_h: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    ra_m: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    ra_s: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    dec_sign: Mapped[Optional[str]] = mapped_column(db.String(1), nullable=True)
    dec_d: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    dec_m: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    dec_s: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # --- Block + Zeile im Block (existieren in SQLite) ---
    block_no: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    row_in_block: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)

    telescope = relationship('Telescope', backref='observation_request_position')
    filterset = relationship('Filterset', backref='observation_request_position')


class ObservationRequestLog(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('observation_request.id'))
    timestamp: Mapped[datetime] = mapped_column(db.DateTime, nullable=True, default=datetime.now(timezone.utc))
    type = db.Column(db.String(10))
    subtype = db.Column(db.String(10))
    text = db.Column(db.String(500))
