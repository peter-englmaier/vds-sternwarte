from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from webapp import db

if TYPE_CHECKING:
    from webapp.model.db.telescope import Telescope


class Filterset(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), nullable=False)
    priority: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    telescope_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('telescope.id'),
        nullable=True
    )
    quantity: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    telescope: Mapped[Optional["Telescope"]] = relationship(
        "Telescope",
        back_populates="filtersets",
        lazy='joined'
    )

    def __repr__(self):
       return f"Filterset('{self.name}')"

    def __str__(self):
       return f"{self.name}"
