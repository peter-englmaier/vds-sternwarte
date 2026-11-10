from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from webapp import db

if TYPE_CHECKING:
    from webapp.model.db.telescope import Telescope


"""
    An observatory is a place with a mount but potentially multiple telescopes on the mount
"""
class Observatory(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False)
    site_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    # telescopes = db.relationship('Telescope', back_populates='observatory', lazy='joined')
    telescopes: Mapped[List["Telescope"]] = relationship(
        'Telescope',
        back_populates='observatory',
        lazy='joined'
    )
    site = db.relationship('Site', back_populates='observatories', lazy='joined')

    def __repr__(self):
        return f"Observatory('{self.name}')"

    def __str__(self):
        return f"{self.name}"
