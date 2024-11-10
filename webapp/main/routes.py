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


@main.route("/calendar")
@login_required
def calendar():
    softwareId = "$Id$"
    version = "0.1-rc"
    return render_template('calendar.html', title='Kalender', version=version, commitId=softwareId)

@main.route("/poweruser")
@login_required
def poweruser():
    softwareId = "$Id$"
    version = "0.1-rc"
    return render_template('poweruser.html', title='Poweruser', version=version, commitId=softwareId)


@main.route("/faq")
def faq():
    softwareId = "$Id$"
    version = "0.1-rc"
    return render_template('faq.html', title='FAQ', version=version, commitId=softwareId)

@main.route("/status")
def status():
    from flask import session
    print(session)
    print(f"{current_user.name=}")
    print(f"Admin User? {current_user.has_role('admin')}")
    return home()
