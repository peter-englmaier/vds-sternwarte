"""Order history of the current user.

Routes::

    GET  /user_order_history  user_order_history()  -> orders_history.html
"""
from flask import render_template, request
from flask_login import current_user, login_required

from webapp.main import main  # blueprint object
from webapp.model.db import Post, ObservationRequest
from webapp.users.utils import role_required


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
    ser_orders = ObservationRequest.query.filter_by(user_id=current_user.id).order_by(ObservationRequest.request_date.desc()).all()
    return render_template("orders_history.html", posts=posts, orders=ser_orders)
