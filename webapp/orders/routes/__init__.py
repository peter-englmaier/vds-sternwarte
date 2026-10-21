"""
Routes of the "orders" blueprint, one module per page or template.
Importing the modules registers their routes on the blueprint.

No module may be named "orders": it would shadow the blueprint exported here.
"""
from webapp.orders import orders  # blueprint object, registered in webapp/__init__.py

from webapp.orders.routes import (
    api,
    order_list,
    create_order,
    edit_order_pos,
    order_positions,
    approval,
    reject_order,
    calendar,
    obs_request_complete,
    feedback,
)
