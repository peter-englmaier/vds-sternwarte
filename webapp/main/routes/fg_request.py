"""Form for an FG request.

The row template aufnahme_zeile.html is also included by create_request_georg.html
via aufnahme_zeile_special.html; both load further rows from /add-row.

Routes::

    GET  /fgrequest  fgrequest()  -> create_obs_request.html
    GET  /add-row    add_row()    -> aufnahme_zeile.html (HTMX)
"""
from flask import render_template
from flask_login import login_required

from webapp.main import main  # blueprint object


# --------------------------------------------------------------------
# FG-Antrag anzeigen
# --------------------------------------------------------------------
@main.route("/fgrequest")
@login_required
def fgrequest():
    """Show the form for an FG request.

    :return: rendered ``create_obs_request.html``.
    """
    return render_template('create_obs_request.html', title='FG Request')


# --------------------------------------------------------------------
# Weitere Aufnahmezeile anhängen
# --------------------------------------------------------------------
@main.route("/add-row")
def add_row():
    """Return one more row for the table of exposures (HTMX).

    .. warning:: The route has no ``login_required``.

    :return: rendered ``aufnahme_zeile.html``.
    """
    return render_template("aufnahme_zeile.html")
