from sqlalchemy.orm import Mapped, mapped_column
from webapp import db


# Aus Altdaten extrahiert
class ObservationHistory(db.Model):
    __tablename__ = 'observation_history'
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    Datum: Mapped[str] = mapped_column(db.String(25), nullable=False)
    Objekt: Mapped[str] = mapped_column(db.String(80), unique=False, nullable=True)
    Rubrik: Mapped[str] = mapped_column(db.String(160), unique=False, nullable=True)
    Teleskop: Mapped[str] = mapped_column(db.String(100), unique=False, nullable=True)
    EinzelbelichtungSekunden: Mapped[str] = mapped_column(db.String(60), unique=False, nullable=True)
    Bildanzahl: Mapped[str] = mapped_column(db.String(5), unique=False, nullable=True)
    Filter: Mapped[str] = mapped_column(db.String(60), unique=False, nullable=True)
    Bildersteller: Mapped[str] = mapped_column(db.String(80), unique=False, nullable=True)
    Observer: Mapped[str] = mapped_column(db.String(80), unique=False, nullable=True)
    NeuentdeckteKleinplaneten: Mapped[str] = mapped_column(db.String(80), unique=False, nullable=True)
