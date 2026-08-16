from flask import render_template, request, url_for, redirect, flash, abort
from markupsafe import escape
from flask_login import login_required
from flask_login import current_user
from sqlalchemy import select
from webapp import Config
from webapp.main import main
from webapp.model.db import db, Post, SystemParameters, ObservationRequest, PoweruserMeldung, User, Group
from webapp.orders.constants import USER_ROLE_ADMIN, USER_ROLE_APPROVER, USER_ROLE_USER, USER_ROLE_GUEST,ORDER_STATUS_LABELS, ORDER_STATUS_WAITING, \
    ORDER_STATUS_PU_REJECTED, ORDER_STATUS_PU_ACCEPTED, ORDER_STATUS_APPROVED, ORDER_STATUS_PU_ASSIGNED
from collections import defaultdict
from ..users.utils import role_required

@main.route("/")
@main.route("/home")
def home():
    if not current_user.is_authenticated or current_user.has_role(USER_ROLE_GUEST):
        return render_template("home.html")
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template("home_intern.html", posts=posts)

# -------------------------------------------------------------
#
# -------------------------------------------------------------
@main.route("/poweruser", methods=['GET','POST'])
@login_required
@role_required("poweruser")
def poweruser():

    if request.method == "POST":
        action = request.form.get("action")
        if action != "pu_meldung":
            return '<span id="pu-feedback-0" class="text-danger ms-2">Unbekannte Aktion</span>', 400

        order_id = request.form.get("order_id", type=int)
        availability = request.form.get("availability", type=int)

        order_id_html = escape(str(order_id or 0))

        if not order_id or availability not in (1, 2, 3, 4):
            return (
                f'<span id="pu-feedback-{order_id_html}" class="text-danger ms-2">Ungültige Eingabe</span>',
                400,
            )

        order = ObservationRequest.query.get_or_404(order_id)

        is_assigned_to_current_user = (
        order.status == ORDER_STATUS_PU_ASSIGNED
        and order.request_poweruser_id == current_user.id
        )

        meldung = PoweruserMeldung.query.filter_by(
            observation_request_id=order_id,
            poweruser_user_id=current_user.id
        ).first()

                # 4 = Keine Rückmeldung
        if availability == 4:
            if meldung is not None:
                db.session.delete(meldung)

            db.session.commit()

            positive_feedback_count = PoweruserMeldung.query.filter(
                PoweruserMeldung.observation_request_id == order_id,
                PoweruserMeldung.availability.in_([1, 2])
            ).count()

            if positive_feedback_count == 1:
                count_text = "Es hat bereits 1 PU zurückgemeldet."
            elif positive_feedback_count > 1:
                count_text = f"Es haben bereits {positive_feedback_count} PUs zurückgemeldet."
            else:
                count_text = ""

            return (
                f'<span id="pu-feedback-{order_id_html}">'
                f'<div class="mt-1">'
                f'<span class="text-muted">'
                f'Keine Rückmeldung eingereicht'
                f'</span>'
                f'</div>'
                f'</span>'
                f'<div id="pu-count-{order_id_html}" '
                f'class="text-muted mt-1" '
                f'hx-swap-oob="innerHTML">'
                f'{count_text}'
                f'</div>'
            )

        if meldung is None:
            meldung = PoweruserMeldung(
                observation_request_id=order_id,
                poweruser_user_id=current_user.id,
                availability=availability
            )
            db.session.add(meldung)
        else:
            meldung.availability = availability

# Bereits zugewiesener Poweruser kann den Termin doch nicht wahrnehmen
        if is_assigned_to_current_user and availability == 3:
            order.status = ORDER_STATUS_PU_REJECTED

        db.session.commit()

        positive_feedback_count = PoweruserMeldung.query.filter(
            PoweruserMeldung.observation_request_id == order_id,
            PoweruserMeldung.availability.in_([1, 2])
        ).count()

        if positive_feedback_count == 1:
            count_text = "Es hat bereits 1 PU zurückgemeldet."
        elif positive_feedback_count > 1:
            count_text = f"Es haben bereits {positive_feedback_count} PUs zurückgemeldet."
        else:
            count_text = ""

        return (
    f'<span id="pu-feedback-{order_id_html}">'
    f'<div class="mt-1">'
    f'<span class="text-success">'
    f'Rückmeldung ist eingereicht'
    f'</span>'
    f'<br>'
    f'<small class="text-muted">'
    f'Die Antwort kann bis zur Zuweisung durch den Approver geändert werden:'
    f'</small>'
    f'</div>'
    f'</span>'
    f'<div id="pu-count-{order_id_html}" '
    f'class="text-muted mt-1" '
    f'hx-swap-oob="innerHTML">'
    f'{count_text}'
    f'</div>'
        )

    # GET
    stmt = (
        select(ObservationRequest, User)
        .outerjoin(
            User,
            User.id == ObservationRequest.request_poweruser_id,
        )
        .where(
            ObservationRequest.status.in_([
                ORDER_STATUS_APPROVED,
                ORDER_STATUS_PU_ASSIGNED,
            ])
        )    
        .order_by(
            ObservationRequest.request_date,
            ObservationRequest.id,
        )
    )
    all_rows = db.session.execute(stmt).unique().all()

    open_orders = []
    own_orders = []
    others_orders = []

    my_meldungen_by_order = {
        meldung.observation_request_id: meldung.availability
        for meldung in PoweruserMeldung.query.filter_by(
            poweruser_user_id=current_user.id
        ).all()
    }
    
    for order, pu_user in all_rows:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")

        order.positive_feedback_count = PoweruserMeldung.query.filter(
            PoweruserMeldung.observation_request_id == order.id,
            PoweruserMeldung.availability.in_([1, 2])
        ).count()

        if order.status == ORDER_STATUS_APPROVED:
            # Noch nicht zugewiesene Anträge
            order.poweruser_name = (
                pu_user.display_name()
                if pu_user
                else None
            )
            order.my_pu_meldung_availability = my_meldungen_by_order.get(order.id)
            open_orders.append(order)

        elif order.status == ORDER_STATUS_PU_ASSIGNED:
            order.poweruser_name = (
                pu_user.display_name()
                if pu_user
                else None
            )

            if order.request_poweruser_id == current_user.id:
                order.my_pu_meldung_availability = my_meldungen_by_order.get(order.id)
                own_orders.append(order)
            else:
                others_orders.append(order)

    return render_template("poweruser.html",title="Poweruser",open_orders=open_orders,own_orders=own_orders,others_orders=others_orders,)

# -------------------------------------------------------------
#
# -------------------------------------------------------------
@main.route("/approver", methods=["GET"])
@login_required
@role_required("approver")
def approver():

    all_orders = (
        ObservationRequest.query
        .filter(ObservationRequest.status.in_([ORDER_STATUS_WAITING, ORDER_STATUS_APPROVED, ORDER_STATUS_PU_ASSIGNED, ORDER_STATUS_PU_REJECTED, ORDER_STATUS_PU_ACCEPTED]))
        .all()
    )

    # Action-required-Anträge ganz nach oben
    all_orders.sort(
    key=lambda order: order.status != ORDER_STATUS_PU_REJECTED
    )

    for order in all_orders:
        order.status_label = ORDER_STATUS_LABELS.get(order.status, "??")

        # Zugewiesener Poweruser kann Termin nicht mehr wahrnehmen
        if order.status == ORDER_STATUS_PU_REJECTED:
            order.status_label = "Action required"

        if order.request_poweruser_id:
            order.poweruser_name = User.query.get(order.request_poweruser_id).display_name()

    order_ids = [o.id for o in all_orders]

    pu_meldungen_by_order = defaultdict(list)
    if order_ids:
        rows = (
            db.session.query(
                PoweruserMeldung.observation_request_id,
                PoweruserMeldung.poweruser_user_id,
                PoweruserMeldung.availability,
                User.name,
                User.firstname,
                User.surname,
            )
            .join(User, User.id == PoweruserMeldung.poweruser_user_id)
            .filter(PoweruserMeldung.observation_request_id.in_(order_ids))
            .all()
        )

        for r in rows:
            display_name = User.query.get(r[1]).display_name()
            pu_meldungen_by_order[r.observation_request_id].append({
                "user_id": r.poweruser_user_id,
                "name": display_name or f"User {r.poweruser_user_id}",
                "availability": r.availability,
            })

    return render_template("approver.html", orders=all_orders, pu_meldungen_by_order=pu_meldungen_by_order)

# -------------------------------------------------------------
#
# -------------------------------------------------------------
@main.route("/faq")
def faq():
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    return render_template('faq.html', title='FAQ', vds_link=vds_link)

# issue #116 About in Menüleiste
@main.route("/about")
def about():
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    commit = Config.GITCOMMIT

    # when running outside docker, we read git commit hash from local git
    if [ commit == "" ]:
            try:
                import git
                repo = git.Repo(search_parent_directories=True)
                commit = repo.head.object.hexsha[0:7]
            except Exception as e:
                print(e)

    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    if Config.APPVERSION != "":
        version = f"{Config.APPVERSION}"
    else:
        version = f"keine"
    isDirty = Config.CLEANBUILD != "true"
    if Config.ENVIRONMENT == "LOCAL":
        server = "Running on your local machine"
    else:
        server = f"{Config.ENVIRONMENT}"
    return render_template('about.html', title='About', vds_link=vds_link, version=version, server=server, commit=commit, isDirty=isDirty)

@main.route("/status")
def status():
    from flask import session
    print(session)
    print(f"{current_user.name=}")
    print(f"Admin User? {current_user.has_role(USER_ROLE_ADMIN)}")
    print( "Du bist" + f" current_user.groups")
    return home()

@main.route("/fgrequest")
@login_required
def fgrequest():
    return render_template('create_obs_request.html', title='FG Request')

@main.route("/servicerequest")
@login_required
def servicerequest():
    return render_template('create_service.html', title='Service Request')

@main.route("/request_georg")
@login_required
def request_georg():
    return render_template('create_request_georg.html', title='Request Georg')

@main.route("/add-row")
def add_row():
    return render_template("aufnahme_zeile.html")

# -------------------------------------------------------------
@main.route("/gast", methods=["GET"])
@login_required
def gast():

    if not (
        current_user.has_role(USER_ROLE_ADMIN)
        or current_user.has_role(USER_ROLE_APPROVER)
    ):
        abort(403)

    guest_group = Group.query.filter_by(
        name=f"{USER_ROLE_GUEST}_group"
    ).first()

    pending_users = []

    if guest_group:
        pending_users = (
            User.query.join(User.groups)
            .filter(Group.id == guest_group.id)
            .all()
        )

    #Benutzer ohne Gruppenzuordnung
    no_group = [u for u in User.query.all() if not u.groups]
    pending_ids = {u.id for u in pending_users}
    pending_users.extend([u for u in no_group if u.id not in pending_ids])

    return render_template(
        "gast.html",
        title="Neue Benutzer freischalten",
        pending_users=pending_users,
    )


@main.route("/gast/approve", methods=["POST"])
@login_required
def gast_approve():

    if not (
        current_user.has_role(USER_ROLE_ADMIN)
        or current_user.has_role(USER_ROLE_APPROVER)
    ):
        abort(403)

    user_id = request.form.get("user_id", type=int)
    if not user_id:
        flash("Fehlende user_id", "danger")
        return redirect(url_for("main.gast"))

    user = User.query.get_or_404(user_id)

    guest_group = Group.query.filter_by(
        name=f"{USER_ROLE_GUEST}_group"
    ).first()
    user_group = Group.query.filter_by(
        name=f"{USER_ROLE_USER}_group"
    ).first()

    if not user_group:
        flash("Systemfehler: user_group existiert nicht.", "danger")
        return redirect(url_for("main.gast"))

    if guest_group and guest_group in user.groups:
        user.groups.remove(guest_group)

    if user_group not in user.groups:
        user.groups.append(user_group)

    db.session.commit()

    flash(f"{user.name} wurde freigeschaltet.", "success")
    return redirect(url_for("main.gast"))

@main.route("/impressum")
def impressum():
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    return render_template('impressum.html', title='Impressum', vds_link=vds_link)
