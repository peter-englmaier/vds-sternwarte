"""JSON endpoints for the javascript of the order pages.

Routes::

    GET   /orders/user_preference                      get_user_preference()  -> JSON
    POST  /orders/user_preference                      set_user_preference()  -> JSON
    GET   /orders/get_telescopes/<int:observatory_id>  get_telescopes()       -> JSON
    POST  /orders/get_filtersets                       get_filtersets()       -> JSON
"""
from flask import request, jsonify, abort
from flask_login import current_user, login_required

from webapp.orders import orders  # blueprint object
from webapp.orders.orderform import telescope_query, filterset_query
from webapp.orders.orderservices import set_user_preference_service, get_user_preference_service
from webapp.users.utils import role_required


class ValidUserPrefKey(str):
    """str-like class, but only accepts valid chars"""
    VALID_SET = set("abcdefghijklmnopqrstuvwxyz0123456789._-")

    def __init__(self, id: str=""):
        if set(id.lower()) - self.VALID_SET != set():       # chars not in VALID_SET
            raise ValueError("illegal id string")
        super().__init__()
        self = id


class ValidUserPrefValue(str):
    """str-like class, but only accepts valid chars"""
    VALID_SET = set("abcdefghijklmnopqrstuvwxyz0123456789 ._-")

    def __init__(self, id: str=""):
        if set(id.lower()) - self.VALID_SET != set():       # chars not in VALID_SET
            raise ValueError("illegal id string")
        super().__init__()
        self = id



# ------------------------------------------------------------------
# User preference laden
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["GET"])
@login_required
@role_required("user")
def get_user_preference():
    """Return a preference of the current user as JSON.

    The query parameter ``key`` names the preference.

    :return: JSON ``{"success": true, "value": ...}``; ``value`` is ``false``
        if the preference is not set.
    """
    try:
        key = ValidUserPrefKey(request.args.get("key"))
    except ValueError:
        abort(500)

    value = get_user_preference_service(current_user.id, key, False)
    return jsonify(success=True, value=value)


# ------------------------------------------------------------------
# User preference speichern
# ------------------------------------------------------------------
@orders.route("/orders/user_preference", methods=["POST"])
@login_required
@role_required("user")
def set_user_preference():
    """Store a preference of the current user.

    Expects a JSON body with ``key``, ``value`` and optionally ``default``.

    :return: JSON ``{"success": true}``, or ``{"success": false, "error": ...}``
        with status 500 if saving failed.
    """
    data = request.get_json()
    try:
        key = ValidUserPrefKey(data.get("key"))
        value = ValidUserPrefValue(data.get("value"))
    except ValueError:
        abort(500)

    status, message = set_user_preference_service(current_user.id, key, value)

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
@login_required
@role_required("user")
def get_telescopes(observatory_id):
    """Return the telescopes of an observatory as JSON.

    :param observatory_id: id of the observatory.
    :return: JSON list of ``{"id": ..., "name": ...}``.
    """
    telescopes = telescope_query(observatory_id)
    return jsonify([{'id': t.id, 'name': t.name} for t in telescopes])


# --------------------------------------------------------------
# Filtersets zum Teleskop
# --------------------------------------------------------------
@orders.route("/orders/get_filtersets", methods=["POST"])
@login_required
@role_required("user")
def get_filtersets():
    """Return the filter sets of a telescope as JSON.

    Expects a JSON body with ``telescope_id``.

    :return: JSON list of ``{"id": ..., "name": ...}``.
    """
    data = request.get_json()
    try:
        telescope_id = int(data.get("telescope_id"))
    except ValueError:
        abort(500)

    filtersets = filterset_query(telescope_id)
    return jsonify([{"id": f.id, "name": f.name} for f in filtersets])
