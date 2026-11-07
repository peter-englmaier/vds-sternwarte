from datetime import datetime, date, timedelta
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column
from webapp import db

if TYPE_CHECKING:
    from webapp.model.db.observatory import Observatory
    from webapp.model.db.observation_request import ObservationRequest


"""
ObservatoryReservation: a Reservation class for observatories
date: the reservation day (actually the night), time is always 12:00 (noon)
"""
class ObservatoryReservation(db.Model):
    # status values
    class Status(Enum):
        UNDEF    = 1 # status is undefined
        RESERVED = 2 # date is reserved, but not yet finally booked
        BOOKED   = 3 # date is booked
        EXPIRED  = 4 # reservation expired
        FROZEN   = 5 # reservation is not final, but it has been submitted

    # reservation constants
    reservation_maxtime = timedelta(minutes=4320) # how long can a date be reserved without submission
    reservation_time = timedelta(minutes=1440) # how long a single reservation lasts without refresh

    __tablename__ = 'observatory_reservation'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, unique=True)
    observatory_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('observatory.id'), nullable=False)
    observation_request_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('observation_request.id'), nullable=False)
    reservation_max: Mapped[datetime] = mapped_column(db.DateTime)
    reservation_exp: Mapped[datetime] = mapped_column(db.DateTime)
    status: Mapped[str] = mapped_column(db.String(10), nullable=False, default=Status.UNDEF.name)

    def __repr__(self):
        return f"ObservatorReservation('{self.observatory_id}, '{self.date}', '{self.status}', '{self.reservation_exp}')"

    def __str__(self):
        s = self.Status[self.status]
        date_string = self.date.strftime('%d.%m.%Y')
        if s == self.Status.RESERVED:
            exp_string = self.reservation_exp.strftime('%d.%m.%Y %H:%M')
            return f"{date_string} reserviert bis {exp_string}"
        elif s == self.Status.EXPIRED:
            return f"Reservierung ist abgelaufen"
        elif s == self.Status.BOOKED:
            return f"{date_string} definitiv reserviert"
        elif s == self.Status.FROZEN:
            return f"{date_string} provisorisch reserviert"
        else:
            return f"Status unbekannt"

    """
    date_sanitize: strip time and timezone from date
    """
    @staticmethod
    def date_sanitize(adate: datetime):
        if isinstance(adate, date):
            return adate
        else:
            return adate.date()

    def __init__(
        self,
        date: datetime,
        observatory: "Observatory",
        request: "ObservationRequest",
    ):
        self.date = self.date_sanitize(date)
        self.observatory_id = observatory.id
        self.observation_request_id = request.id
        now = datetime.now()
        self.reservation_max = now + self.reservation_maxtime
        self.reservation_exp = now + self.reservation_time
        self.status = self.Status.RESERVED.name

    def refresh(self):
        """Extend the reservation if possible"""
        if self.status == self.Status.RESERVED.name:
            now = datetime.now()
            self.reservation_exp = max(self.reservation_max, now + self.reservation_time)
            if self.reservation_exp < now:
                self.status = self.Status.EXPIRED.name

    def cancel(self):
        """Cancel the reservation"""
        self.status = self.Status.EXPIRED.name

    def freeze(self):
        """Freeze the reservation - will no longer expire"""
        if self.status == self.Status.RESERVED.name:
            self.status = self.Status.FROZEN.name

    def confirm(self):
        """Confirm the reservation (fully booked)"""
        self.status = self.Status.BOOKED.name

    def is_booked(self):
        """Date is fully booked"""
        return self.status == self.Status.BOOKED.name

    def is_frozen(self):
        """Reservation will not expire, but is not yet fully booked"""
        return self.status == self.Status.FROZEN.name

    def is_expired(self):
        """Reservation has expired and is no longer valid"""
        now = datetime.now()
        if self.status == self.Status.RESERVED.name and self.reservation_exp < now:
            self.status = self.Status.EXPIRED.name
        return self.status == self.Status.EXPIRED.name

    def set_date(self, newdate):
        """change reservation date - will reset reservation period"""
        newdate = self.date_sanitize(newdate)
        olddate = self.date.date()
        if olddate != newdate:
            self.date = newdate
            now = datetime.now()
            self.reservation_max = now + self.reservation_maxtime
            self.reservation_exp = now + self.reservation_time
            self.status = self.Status.RESERVED.name
        return self

    def set_observatory(self, observatory):
        """change observatory - will reset reservation period"""
        if self.observatory_id != observatory.id:
            self.observatory_id = observatory.id
            now = datetime.now()
            self.reservation_max = now + self.reservation_maxtime
            self.reservation_exp = now + self.reservation_time
            self.status = self.Status.RESERVED.name
        return self


Status = ObservatoryReservation.Status
