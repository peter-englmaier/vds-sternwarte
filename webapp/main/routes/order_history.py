"""Order history of the current user.

Routes::

    GET  /user_order_history  user_order_history()  -> orders_history.html
"""
from flask import render_template, request
from flask_login import current_user, login_required

from webapp.main import main  # blueprint object
from webapp.model.db import Post, User, ObservationRequest, ObservatoryReservation
from webapp.users.utils import role_required
from webapp.orders.constants import ORDER_STATUS_LABELS


# --------------------------------------------------------------------
# Historie der eigenen Anträge anzeigen
# --------------------------------------------------------------------
@main.route("/user_order_history")
@login_required
@role_required("user")
def user_order_history():
    """Show all orders of the current user, newest first.

    Also passes the latest posts, three per page (query parameter ``page``).

    :return: rendered ``orders_history.html``.
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)

    user_orders = ObservationRequest.query.filter_by(user_id=current_user.id).order_by(ObservationRequest.request_date.desc()).all()
    for order in user_orders:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")
        reservation = ObservatoryReservation.query.filter_by(observation_request_id=order.id).first();
        order.date_is_reserved = reservation is not None
        order.date_info = order.request_date.strftime('%d.%m.%Y')
        pwuser = User.query.get(order.request_poweruser_id)
        if pwuser:
            order.poweruser_name = pwuser.display_name()

    return render_template("orders_history.html", posts=posts, orders=user_orders)
