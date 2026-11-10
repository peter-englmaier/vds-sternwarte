from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from webapp import db

if TYPE_CHECKING:
    from webapp.model.db.observatory import Observatory
    from webapp.model.db.filterset import Filterset


"""
    A telescope is an Optical Tube Assembly consisting of telescope and camera
"""
class Telescope(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False)
    observatory_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('observatory.id'),
        nullable=True
    )
    aperature_mm: Mapped[float] = mapped_column(db.Float, nullable=False)
    focal_length_mm: Mapped[float] = mapped_column(db.Float, nullable=False)
    camera_name: Mapped[str] = mapped_column(db.String(30), nullable=False)
    status: Mapped[str] = mapped_column(db.String(2), nullable=False, default="0")
    observatory: Mapped[Optional["Observatory"]] = relationship(
        'Observatory',
        back_populates='telescopes',
        lazy='joined'
    )
    filtersets: Mapped[List["Filterset"]] = relationship(
        'Filterset',
        back_populates='telescope',
        cascade='all, delete-orphan',
        lazy='joined'
    )
    def __repr__(self):
       return f"Telescope('{self.name}')"

    def __str__(self):
       return f"{self.name}"
