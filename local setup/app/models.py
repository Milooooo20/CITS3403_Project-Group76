from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login  # `db` is SQLAlchemy instance, `login` is LoginManager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    playlist = db.relationship('Playlist', backref='owner', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_or_create_playlist(self):
        if self.playlist is None:
            playlist = Playlist(user_id=self.id, name=f"{self.username}'s Playlist")
            db.session.add(playlist)
            db.session.commit()
            self.playlist = playlist
        return self.playlist

# Required by Flask-Login to load the user
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    songs = db.relationship('Song', backref='playlist', lazy='dynamic', cascade='all, delete-orphan')


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(64), index=True)
    title = db.Column(db.String(128))
    artist = db.Column(db.String(128))
    album = db.Column(db.String(128))
    album_art = db.Column(db.String(256))
    preview_url = db.Column(db.String(256))
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'))
