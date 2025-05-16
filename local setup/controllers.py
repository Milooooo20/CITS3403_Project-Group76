from flask import request
from app import db
from app.models import Playlist, User


def logging_in(id, username, password):
    user = db.session.get(User, id)
    if user and user.check_password(password):
        #login_user(user)
        return "redirect(url_for('main.profile'))"

    #flash('Invalid username or password', 'error')
    return "redirect(url_for('main.sign_in'))"


def signing_up(username, email, password, confirm_pw):
    if password != confirm_pw:
        #flash('Passwords do not match', 'error')
        return "confirm_pw: redirect(url_for('main.create_account'))"

    if User.query.filter((User.username == username) | (User.email == email)).first():
        #flash('Username or email already exists', 'error')
        return "same_credential: redirect(url_for('main.create_account'))"

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    playlist = Playlist(user_id=new_user.id, name=f"{new_user.username}'s Playlist")
    db.session.add(playlist)
    db.session.commit()

    #flash('Account created successfully. Please sign in.', 'success')
    return "redirect(url_for('main.sign_in'))"