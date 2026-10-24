"""Form for a block request of the telescope Georg.

Routes::

    GET  /request_georg  request_georg()  -> create_request_georg.html
"""
from flask import render_template
from flask_login import login_required

from webapp.main import main  # blueprint object


# --------------------------------------------------------------------
# Blockfunktion Georg anzeigen
# --------------------------------------------------------------------
@main.route("/request_georg")
@login_required
def request_georg():
    """Show the form for a block request of Georg.

    :return: rendered ``create_request_georg.html``.
    """
    return render_template('create_request_georg.html', title='Request Georg')
