"""Static page that explains the order statuses and their flow.

Linked from the "Status" column header in orders.html.

Routes::

    GET   /orders/status  status_flow()  -> status_flow.html
"""
from flask import render_template
from flask_login import login_required

from webapp.orders import orders  # blueprint object


# --------------------------------------------------------------------
# Ablauf der Antragsstati anzeigen
# --------------------------------------------------------------------
@orders.route("/orders/status", methods=["GET"])
@login_required
def status_flow():
    """Show the flow diagram and the description of the order statuses.

    :return: rendered ``status_flow.html``.
    """
    return render_template("status_flow.html", title="Ablauf eines Antrags")
