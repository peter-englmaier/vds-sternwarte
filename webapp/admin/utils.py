from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_login import current_user

def names(groups):
    if groups:
        str = groups[0].name
        for g in groups[1:]:
            str += f", {g.name}"
        return str
    else:
        return "None"


class GenericModelView(ModelView):
    page_size = 50  # the number of entries to display on the list view
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_hide_backrefs = False
    can_export = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('home', next=request.url))

class UserModelView(GenericModelView):
    column_list = ('name', 'surname', 'firstname', 'email', 'vds_number', 'groups')
    column_exclude_list = ['password', ]
    form_excluded_columns = ['password', ]
    # column_descriptions = dict(
    #     name='Username',
    # )
    column_labels = dict(
        name='Username',
        surname='Surname',
        firstname="First name",
        email="Email",
        vds_number="VdS Number",
        groups="Groups",
    )
    column_formatters = dict(
        groups=(lambda v, c, m, p: names(m.groups)), # format group list
    )



class GroupModelView(GenericModelView):
    column_list = ('name', 'roles')
    # column_descriptions = dict(
    #     name='Name of group',
    # )
    column_formatters = dict(
        roles=(lambda v, c, m, p: names(m.roles)), # format role list
    )

class RoleModelView(GenericModelView):
    column_list = ('name', 'groups')
    # column_descriptions = dict(
    #     name='Name of role',
    # )
    column_formatters = dict(
        groups=(lambda v, c, m, p: names(m.groups)), # format group list
    )

class SiteModelView(GenericModelView):
    column_list = ('name', 'longitude', 'lattitude', 'observatories')
    # column_descriptions = dict(
    #     name='Name of role',
    # )
    # column_formatters = dict(
    #     groups=(lambda v, c, m, p: names(m.groups)), # format group list
    # )

class ObservatoryModelView(GenericModelView):
    column_list = ('name', 'telescopes')
    column_formatters = dict(
        groups=(lambda v, c, m, p: names(m.sites)), # format group list
    )

class TelescopeModelView(GenericModelView):
    column_list = ('name', 'observatory')


class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

def init_admin(app, admin):
    from webapp import db
    from webapp.models import User, Group, Role, Site, Observatory, Telescope

    admin.init_app(app, index_view=MyHomeView())
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(GroupModelView(Group, db.session))
    admin.add_view(RoleModelView(Role, db.session))
    admin.add_view(SiteModelView(Site, db.session))
    admin.add_view(ObservatoryModelView(Observatory, db.session))
    admin.add_view(TelescopeModelView(Telescope, db.session))
