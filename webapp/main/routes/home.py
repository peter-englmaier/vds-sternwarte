"""Start page.

Routes::

    GET  /         home()    -> home.html (anonymous, guest), home_intern.html
    GET  /home     home()    -> home.html (anonymous, guest), home_intern.html
    GET  /status   status()  -> same as /home, prints session info to stdout
"""
from flask import render_template, request
from flask_login import current_user

from webapp.main import main  # blueprint object
from webapp.model.db import Post
from webapp.orders.constants import USER_ROLE_ADMIN, USER_ROLE_GUEST


# --------------------------------------------------------------------
# Startseite
# --------------------------------------------------------------------
@main.route("/")
@main.route("/home")
def home():
    """Show the start page.

    Anonymous users and guests get the public start page. All other users get
    the internal start page with the latest posts, three per page. Query
    parameter ``page`` selects the page of posts.

    :return: rendered ``home.html`` or ``home_intern.html``.
    """
    if not current_user.is_authenticated or current_user.has_role(USER_ROLE_GUEST):
        return render_template("home.html")
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template("home_intern.html", posts=posts)


# --------------------------------------------------------------------
# Debug: Session des Benutzers ausgeben
# --------------------------------------------------------------------
@main.route("/status")
def status():
    """Print the session and the role of the current user to stdout, then
    show the start page.

    .. warning:: Debug route without ``login_required``. For anonymous users,
       ``current_user.name`` raises an :exc:`AttributeError` (status 500). The
       last ``print`` outputs the literal text ``current_user.groups`` instead
       of the groups.

    :return: the response of :func:`home`.
    """
    from flask import session
    print(session)
    print(f"{current_user.name=}")
    print(f"Admin User? {current_user.has_role(USER_ROLE_ADMIN)}")
    print( "Du bist" + f" current_user.groups")
    return home()
