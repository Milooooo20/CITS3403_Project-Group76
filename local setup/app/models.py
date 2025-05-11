from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login  # `db` is SQLAlchemy instance, `login` is LoginManager

shared_data = db.Table(
    'shared_data',
    db.Column('sharer_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('receiver_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationships for shared data
    shared_with = db.relationship(
        'User',
        secondary=shared_data,
        primaryjoin=(shared_data.c.sharer_id == id),
        secondaryjoin=(shared_data.c.receiver_id == id),
        backref=db.backref('shared_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Required by Flask-Login to load the user
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
