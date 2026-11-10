from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from webapp import db


class PoweruserMeldung(db.Model):
    __tablename__ = "poweruser_meldung"
    __table_args__ = (
        UniqueConstraint("observation_request_id", "poweruser_user_id", name="uq_meldung_request_poweruser"),
        CheckConstraint("availability IN (1,2,3,4)", name="ck_availability_1_2_3_4"),
        {'sqlite_autoincrement': True},
    )
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    observation_request_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("observation_request.id"),
        nullable=False
    )
    poweruser_user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    # 1 = ist möglich, 2 = vielleicht möglich, 3 = nein, 4 = keine Rückmeldung
    availability: Mapped[int] = mapped_column(db.Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    request = relationship("ObservationRequest", lazy="joined")
    poweruser = relationship("User", lazy="joined")
