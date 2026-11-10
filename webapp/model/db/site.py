from sqlalchemy.orm import Mapped, mapped_column
from webapp import db


"""
    A site is a place with one or more observatories
"""
class Site(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    longitude: Mapped[float] = mapped_column(db.Float)
    lattitude: Mapped[float] = mapped_column(db.Float)
    observatories = db.relationship('Observatory', back_populates='site')

    def __repr__(self):
        return f"Site('{self.name}', l={self.longitude}, b={self.lattitude})"

    def __str__(self):
        return f"{self.name}"
