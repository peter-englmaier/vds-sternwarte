from datetime import datetime, timezone
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from webapp import login_manager, db


@login_manager.user_loader
def load_user(user_id):
    is_legacy_session = ":" not in user_id
    try:
        if is_legacy_session:
            user_pk = int(user_id)
            session_version = None
        else:
            raw_user_pk, raw_session_version = user_id.rsplit(":", 1)
            user_pk = int(raw_user_pk)
            session_version = int(raw_session_version)
    except (TypeError, ValueError):
        return None

    user = User.query.get(user_pk)
    if user is None:
        return None
    if is_legacy_session:
        return user if user.session_version == 0 else None
    return user if user.session_version == session_version else None


"""
    A user is an individual. Do not share users.
"""
class User(db.Model, UserMixin):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(60), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    image_file: Mapped[str] = mapped_column(db.String(60), nullable=False, default='default.jpg')
    password: Mapped[str] = mapped_column(db.String(60), nullable=False)
    session_version: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0, server_default='0')
    surname: Mapped[str] = mapped_column(db.String(40), nullable=True)
    firstname: Mapped[str] = mapped_column(db.String(40), nullable=True)
    vds_number: Mapped[int] = mapped_column(db.Integer, nullable=True)
    last_login: Mapped[datetime] = mapped_column(db.DateTime, nullable=True, default=datetime.now(timezone.utc))
    posts = db.relationship('Post', backref='author', lazy=True)
    groups = db.relationship('Group', secondary='user_group', back_populates='users')
    preferences = db.relationship('UserPreferences', backref='user', cascade="all, delete-orphan")

    def get_id(self):
        return f"{self.id}:{self.session_version}"

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

    @staticmethod
    def by_role(role_name):
        return db.session.query(User).join(User.groups).join(Group.roles).filter(Role.name == role_name).all()

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.image_file}')"

    def __str__(self):
       return f"{self.name}"

    def display_name(self):
        """
        Name of user used for display
        :return: display name
        """
        display = f"{self.firstname or ''} {self.surname or ''}".strip()
        if display == '':
            return self.name
        return display

    def __init__(
        self,
        name: str,
        email: str,
        password: str,
        firstname: str = None,
        surname: str = None,
        vds_number: int = None,
        image_file: str = 'default.jpg',
        last_login: datetime = None
    ):
        self.name = name
        self.email = email
        self.password = password
        self.firstname = firstname
        self.surname = surname
        self.vds_number = vds_number
        self.image_file = image_file
        self.last_login = last_login if last_login is not None else datetime.now(timezone.utc)


class UserPreferences(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    key = db.Column(db.String(100))
    value = db.Column(db.String(100))


"""
    A group is a collection of akin people. At the same time, the group is a collection of
     permissions or "roles" the group can perform. When the people in the group are not "equal",
     it is better to create more groups.
"""
class Group(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False)
    users = db.relationship('User', secondary='user_group', back_populates='groups')
    roles = db.relationship('Role', secondary='role_group', back_populates='groups')

    def has_role(self, name):
        role = Role.query.filter_by(name=name).first()
        if role:
            return role in self.roles
        else:
            print("ERROR: No such role '{}'".format(name))
            return False

    def __repr__(self):
       return f"Group('{self.name}')"

    def __str__(self):
       return f"{self.name}"


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
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False)
    groups = db.relationship('Group', secondary='role_group', back_populates='roles')

    def __repr__(self):
        return f"Role('{self.name}')"

    def __str__(self):
        return f"{self.name}"


role_group = db.Table(
    'role_group',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)


## -----------------------
#  Poweruser
## -----------------------

class Poweruser(db.Model, UserMixin):
    __table_args__ = {'sqlite_autoincrement': True}
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    mobilfone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    fone: Mapped[str] = mapped_column(db.String(20), nullable=True)
    Einweisung: Mapped[str] = mapped_column(db.String(30), nullable=True)
    Status: Mapped[str] = mapped_column(db.String(20), nullable=True)
    last_login: Mapped[datetime] = mapped_column(db.DateTime, nullable=True, default=datetime.now(timezone.utc))

    def __str__(self):
       return f"{self.name}"
