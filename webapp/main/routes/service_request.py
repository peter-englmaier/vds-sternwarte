"""Form for a service request.

Routes::

    GET  /servicerequest  servicerequest()  -> create_service.html
"""
from flask import render_template
from flask_login import login_required

from webapp.main import main  # blueprint object


# --------------------------------------------------------------------
# Wartungsantrag anzeigen
# --------------------------------------------------------------------
@main.route("/servicerequest")
@login_required
def servicerequest():
    """Show the form for a service request.

    :return: rendered ``create_service.html``.
    """
    return render_template('create_service.html', title='Service Request')
