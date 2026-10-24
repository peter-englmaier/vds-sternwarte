"""
Routes of the "main" blueprint, one module per page or template.
Importing the modules registers their routes on the blueprint.

No module may be named "main": it would shadow the blueprint exported here.
"""
from webapp.main import main  # blueprint object, registered in webapp/__init__.py

from webapp.main.routes import (
    home,
    poweruser,
    poweruser_history,
    approver,
    order_history,
    gast,
    fg_request,
    service_request,
    request_georg,
    faq,
    about,
    impressum,
)
