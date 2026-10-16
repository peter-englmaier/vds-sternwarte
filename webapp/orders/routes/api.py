"""JSON endpoints for the javascript of the order pages.

Routes::

    GET   /orders/user_preference                      get_user_preference()  -> JSON
    POST  /orders/user_preference                      set_user_preference()  -> JSON
    GET   /orders/get_telescopes/<int:observatory_id>  get_telescopes()       -> JSON
    POST  /orders/get_filtersets                       get_filtersets()       -> JSON
"""
from flask import request, jsonify
from flask_login import current_user, login_required

from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import telescope_query, filterset_query
from webapp.orders.orderservices import set_user_preference_service, get_user_preference_service


# ------------------------------------------------------------------
# User preference laden
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["GET"])
@login_required
def get_user_preference():
    """Return a preference of the current user as JSON.

    The query parameter ``key`` names the preference.

    :return: JSON ``{"success": true, "value": ...}``; ``value`` is ``false``
        if the preference is not set.
    """
    key = request.args.get("key")
    value = get_user_preference_service(current_user.id, key, False)
    return jsonify(success=True, value=value)


# ------------------------------------------------------------------
# User preference speichern
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["POST"])
@login_required
def set_user_preference():
    """Store a preference of the current user.

    Expects a JSON body with ``key``, ``value`` and optionally ``default``.

    :return: JSON ``{"success": true}``, or ``{"success": false, "error": ...}``
        with status 500 if saving failed.
    """
    data = request.get_json()
    key = data.get("key")
    value = data.get("value")
    default = data.get("default")  # falls benötigt

    status, message = set_user_preference_service(current_user.id, key, value, default)

    if status == 1:
        # Fehlerfall
        print(f"ERROR: {message}")
        return jsonify(success=False, error="Ein fehler ist aufgetreten; siehe logfile."), 500
    else:
    # Erfolg
        return jsonify(success=True)


# --------------------------------------------------------------
# Teleskope zum Observatorium
# --------------------------------------------------------------
@orders.route('/orders/get_telescopes/<int:observatory_id>')
def get_telescopes():
    """Return the telescopes of an observatory as JSON.

    .. warning:: The route passes ``observatory_id`` from the URL, but the
       function takes no parameter and reads the id from a JSON body instead.
       Calling the route currently raises a :exc:`TypeError` (status 500).

    :return: JSON list of ``{"id": ..., "name": ...}``.
    """
    data = request.get_json()
    observatory_id = data.get('observatory_id')
    telescopes = telescope_query(observatory_id)
    return jsonify([{'id': t.id, 'name': t.name} for t in telescopes])


# --------------------------------------------------------------
# Filtersets zum Teleskop
# --------------------------------------------------------------
@orders.route("/orders/get_filtersets", methods=["POST"])
@login_required
def get_filtersets():
    """Return the filter sets of a telescope as JSON.

    Expects a JSON body with ``telescope_id``.

    :return: JSON list of ``{"id": ..., "name": ...}``.
    """
    data = request.get_json()
    telescope_id = data.get("telescope_id")
    filtersets = filterset_query(telescope_id)
    return jsonify([{"id": f.id, "name": f.name} for f in filtersets])
