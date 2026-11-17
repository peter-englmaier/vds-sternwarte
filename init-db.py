#!/usr/bin/env python
from flask_migrate import upgrade
from webapp import create_app, db
from webapp.model.db import Site, Telescope, Observatory, Filterset
import sys
from sqlalchemy import text

app=create_app()

with app.app_context():
    
 # Verknüpfungsspalte Orginalantrag zu Feedback/Rückmeldungskopie
    if "--add-feedback-link" in sys.argv:
        if db.engine.dialect.name != "postgresql":
            raise SystemExit(
                "Abbruch: Dieser Modus ist für PostgreSQL vorgesehen."
            )

        with db.engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE observation_request
                ADD COLUMN IF NOT EXISTS source_request_id INTEGER
                REFERENCES observation_request(id)
                UNIQUE
            """))

        with db.engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE observation_request
                ADD COLUMN IF NOT EXISTS copied_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS completed_by_id INTEGER
                    REFERENCES "user"(id),
                ADD COLUMN IF NOT EXISTS matches_request BOOLEAN,
                ADD COLUMN IF NOT EXISTS deviations VARCHAR(2000)
            """))

        print("Verknüpfungsspalte ist vorhanden.")
        raise SystemExit(0)
    
    #db.create_all()
    upgrade() # Fix DB migration issues.

    # SITE
    name='Astro-Farm Hakos, Namibia'
    hakos=Site.query.filter_by(name = name).first()
    if not hakos:
        hakos=Site(name=name, longitude= 16.36667, lattitude = -23.23333)
        db.session.add(hakos)   # TELESCOPES
        db.session.commit()

    # TELESCOPES
    name='TS 12" Newton-Astrograph'
    newton=Telescope.query.filter_by(name = name).first()
    if not newton:
        newton=Telescope(name=name, focal_length_mm = 1391, aperature_mm = 305,
                         camera_name = 'ToupTek Mono 2600MP G2')
        db.session.add(newton)
        db.session.commit()

    name='Takahashi Epsilon 160ED'
    tak=Telescope.query.filter_by(name = name).first()
    if not tak:
        tak=Telescope(name=name, focal_length_mm = 530, aperature_mm = 160,
                         camera_name = 'Lacerta DeepSkyPro 2600c')
        db.session.add(tak)
        db.session.commit()


    # OBSERVATORY
    name='VdS Remotesternwarte'
    observatory = Observatory.query.filter_by(name = name).first()
    if not observatory:
        observatory = Observatory(name=name, site_id=hakos.id)
        db.session.add(observatory)
        db.session.commit()

    # Add telescopes to observatory
    for scope in [newton, tak]:
        if scope not in observatory.telescopes:
            observatory.telescopes.append(scope)
            db.session.add(observatory)
            db.session.commit()

    # FILTER
    filters={ 'L-1', 'R', 'G', 'B', 'Ha (6nm)', 'OIII (6nm)', 'SII (6nm)'}
    for f in filters:
        filter=Filterset.query.filter_by(name=f, telescope_id=newton.id).first()
        if not filter:
            filter=Filterset(name=f, telescope_id=newton.id)
            db.session.add(filter)
            db.session.commit()
    filters={ 'L', 'Triband RGB', 'ALP-T Dual (5nm)', 'SII (3nm)', 'L-eNhance'  }
    for f in filters:
        filter=Filterset.query.filter_by(name=f, telescope_id=tak.id).first()
        if not filter:
            filter=Filterset(name=f, telescope_id=tak.id)
            db.session.add(filter)
            db.session.commit()


print("Database has been initialized")
