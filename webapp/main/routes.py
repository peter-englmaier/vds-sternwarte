from flask import render_template, request
from flask_login import login_required
from flask_login import current_user
from webapp.main import main
from webapp.model.db import Post

@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@main.route("/about")
@login_required
def about():
    software_id = "$Id$"
    version = "0.1-rc"
    return render_template('about.html', title='About', version=version, commitId=software_id)

@main.route("/status")
def status():
    from flask import session
    print(session)
    print(f"{current_user.name=}")
    print(f"Admin User? {current_user.has_role('admin')}")
    return home()

@main.route("/fgrequest")
@login_required
def fgrequest():
    return render_template('create_obs_request.html', title='FG Request')

@main.route("/servicerequest")
@login_required
def servicerequest():
    return render_template('create_service.html', title='Service Request')

@main.route("/vds-newton-add-row")
def vds_newton_add_row():
    return render_template("_vds_newton_aufnahme_zeile.html")

@main.route("/vds-tak-add-row")
def vds_tak_add_row():
    return render_template("_vds_tak_aufnahme_zeile.html")

@main.route("/vds_newton_select")
def vds_newton_select():
    return render_template("_vds_newton_select.html")

@main.route("/vds_newton")
def vds_newton():
    return render_template("_vds_newton.html")

@main.route("/vds_tak_select")
def vds_tak_select():
    return render_template("_vds_tak_select.html")

@main.route("/vds_tak")
def vds_tak():
    return render_template("_vds_tak.html")
