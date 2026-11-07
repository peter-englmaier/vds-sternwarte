from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from webapp import db


class SystemParameters(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    parameter: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(db.String(150), nullable=False)


class SystemParametersHistory(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    parameter: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    value: Mapped[str] = mapped_column(db.String(50), nullable=True)
    history_reason: Mapped[str] = mapped_column(db.String(1))  # I, U, D
    history_timestamp: Mapped[datetime] = mapped_column(db.DateTime, nullable=True, default=datetime.now(timezone.utc))


class MotivationTypes(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    Motivation: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)

    def __str__(self):
       return f"{self.Motivation}"


class ObjectTypes(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    Objecttype: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)

    def __str__(self):
       return f"{self.Objecttype}"
