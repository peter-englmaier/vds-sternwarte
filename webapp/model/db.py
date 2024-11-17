from datetime import datetime, timezone

from itsdangerous import BadSignature, SignatureExpired
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from webapp import login_manager, db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column

'''
    Exception raised when Role does not exist
'''
class RoleDoesNotExist(Exception):
    def __init__(self, name):
        super().__init__(name)
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

"""
    A user is an individual. Do not share users.
"""
class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    image_file: Mapped[str] = mapped_column(db.String(20), nullable=False, default='default.jpg')
    password: Mapped[str] = mapped_column(db.String(60), nullable=False)
    surname: Mapped[str] = mapped_column(db.String(30), nullable=True)
    firstname: Mapped[str] = mapped_column(db.String(30), nullable=True)
    vds_number: Mapped[int] = mapped_column(db.Integer, nullable=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    groups = db.relationship('Group', secondary='user_group', back_populates='users')

    def has_role(self, name):
        for group in self.groups:
            if group.has_role(name):
                return True
        return False

    def get_reset_token(self):
        s = Serializer(secret_key=current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id})
        return token

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(secret_key=current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except BadSignature | SignatureExpired:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.image_file}')"

"""
    A group is a collection of akin people. At the same time, the group is a collection of
     permissions or "roles" the group can perform. When the people in the group are not "equal",
     it is better to create more groups.
"""
class Group(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    users = db.relationship('User', secondary='user_group', back_populates='groups')
    roles = db.relationship('Role', secondary='role_group', back_populates='groups')

    def has_role(self, name):
        role=Role.query.filter_by(name=name).first()
        if role:
            return role in self.roles
        else:
            raise RoleDoesNotExist(name)

    def __repr__(self):
        return f"Group('{self.name}')"


user_group = db.Table(
    'user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

"""
    A role should be defined precisely. If needed, a group can have multiple roles. Ideally, each role would 
    only be checked for in one place of the code. Roles should be grouped together in a group to make assignments
    easier.
"""
class Role(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    groups = db.relationship('Group', secondary = 'role_group', back_populates='roles')

    def __repr__(self):
        return f"Role('{self.name}')"


role_group = db.Table(
    'role_group',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)


class Post(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(100), nullable=False)
    date_posted: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

"""
    A site is a place with one or more observatories
"""
class Site(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    longitude: Mapped[float] = mapped_column(db.Float)
    lattitude: Mapped[float] = mapped_column(db.Float)
    observatories = db.relationship('Observatory', backref='site', lazy=True)

    def __repr__(self):
        return f"Site('{self.name}', l={self.longitude}, b={self.lattitude})"

"""
    An observatory is a place with a mount but potentially multiple telescopes on the mount
"""
class Observatory(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    site_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    telescopes = db.relationship('Telescope', backref='observatory', lazy=True)

    def __repr__(self):
        return f"Observatory('{self.name}')"

"""
    A telescope is an Optical Tube Assembly consisting of telescope and camera
"""
class Telescope(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    observatory_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('observatory.id'), nullable=False)
    aperature_mm: Mapped[float] = mapped_column(db.Float, nullable=False)
    focal_length_mm: Mapped[float] = mapped_column(db.Float, nullable=False)
    camera_name: Mapped[str] = mapped_column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Telescope('{self.name}')"

"""
    An ObservationsRequest is a proposed observation for one or more telescopes
    It is in one of the following states:
        - draft: not yet requested
        - waiting: waiting to be rejected or approved
        - rejected: an rejected proposal can become draft again or simply deleted
        - approved: waiting to be performed
        - documentation needed: the propose was performed and needs to be documented
        - finished: once the observation is documented it is finished
"""
class ObservationsRequest(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    telescope_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('telescope.id'), nullable=False)


