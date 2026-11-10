from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from webapp import db


class CatalogueMeta(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    source: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    description: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    version: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=True)
    license: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    maintainer: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=False)
    equinoxes: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False, default='J2000')
    timestamp: Mapped[datetime] = mapped_column(db.DateTime, nullable=True)


class Catalogue(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    catalogue_meta_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('catalogue_meta.id'), nullable=False)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False)
    long_name: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=True)
    type: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=False)
    ra: Mapped[int] = mapped_column(db.Float, unique=False, nullable=False)
    dec: Mapped[int] = mapped_column(db.Float, unique=False, nullable=False)
