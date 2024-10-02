from datetime import datetime, timezone

from itsdangerous import BadSignature, SignatureExpired
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from webapp import db, login_manager
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
