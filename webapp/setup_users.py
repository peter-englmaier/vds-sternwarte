from sqlalchemy.exc import OperationalError
from .database import db

def setup_users(app, bcrypt):
    # setup admin user, if name and password are set
    # always reset password to configured password
    pwd_complex = len(app.config['ADMIN_USER']) > 3 \
                  and len(app.config['ADMIN_PASSWORD']) > 8 \
                  and sum(c.isupper() for c in app.config['ADMIN_PASSWORD']) > 0 \
                  and sum(c.islower() for c in app.config['ADMIN_PASSWORD']) > 0 \
                  and sum(c.isdigit() for c in app.config['ADMIN_PASSWORD']) > 0

    try:
        if pwd_complex:
            from webapp.models import User, Group, Role

            ctx = app.app_context()
            ctx.push()
            admin_user = User.query.filter_by(name=app.config['ADMIN_USER']).first()
            hashed_password = bcrypt.generate_password_hash(app.config['ADMIN_PASSWORD']).decode('utf-8')
            if admin_user:
                admin_user.password = hashed_password
                admin_user.email = app.config['ADMIN_EMAIL']
                db.session.commit()
            else:
                print(f"INFO: Create new admin user {app.config['ADMIN_USER']}")
                admin_user = User(name=app.config['ADMIN_USER'], email=app.config['ADMIN_EMAIL'], password=hashed_password)
                db.session.add(admin_user)
                db.session.commit()

            # add admin group, if not present, and assign to admin user
            admin_group = Group.query.filter_by(name="admin").first()
            if not admin_group:
                admin_group = Group(name="admin")
                admin_user.groups.append(admin_group)
                db.session.add(admin_group)
                db.session.add(admin_user)
                db.session.commit()
            elif admin_group not in admin_user.groups:
                admin_user.groups.append(admin_group)
                db.session.add(admin_user)
                db.session.commit()

            # add admin role, if not present, and assign to admin group
            admin_role = Role.query.filter_by(name="admin").first()
            if not admin_role:
                admin_role = Role(name="admin")
                admin_group.roles.append(admin_role)
                db.session.add(admin_role)
                db.session.add(admin_group)
                db.session.commit()
            elif admin_role not in admin_group.roles:
                admin_group.roles.append(admin_role)
                db.session.add(admin_group)
                db.session.commit()

            db.session.commit()
            ctx.pop()
        else:
            print("WARNING: password is not complex enough, not setting up admin user")
    except OperationalError:
        print("WARNING: Database not initialized")
