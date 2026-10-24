"""Legal notice.

Routes::

    GET  /impressum  impressum()  -> impressum.html
"""
from flask import render_template

from webapp.main import main  # blueprint object
from webapp.model.db import SystemParameters


# --------------------------------------------------------------------
# Impressum anzeigen
# --------------------------------------------------------------------
@main.route("/impressum")
def impressum():
    """Show the legal notice with the link to the VdS website.

    The link comes from the system parameter ``vds_link``, default ``#``.

    :return: rendered ``impressum.html``.
    """
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    return render_template('impressum.html', title='Impressum', vds_link=vds_link)
