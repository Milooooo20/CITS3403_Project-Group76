from flask import render_template, request, redirect, flash, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Playlist, Song
from app.SpotifyApi import SpotifyAPI

def register_routes(app):
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/compare')
    def compare():
        return render_template('compare.html')

    @app.route('/create_account', methods=['GET', 'POST'])
    def create_account():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm-password']

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('create_account'))

            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash('Username or email already exists', 'error')
                return redirect(url_for('create_account'))

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            playlist = Playlist(user_id=new_user.id, name=f"{new_user.username}'s Playlist")
            db.session.add(playlist)
            db.session.commit()

            flash('Account created successfully. Please sign in.', 'success')
            return redirect(url_for('sign_in'))

        return render_template('create_account.html')

    @app.route('/edit_playlist')
    def edit_playlist():
        return render_template('edit_playlist.html')

    @app.route('/profile')
    @login_required
    def profile():
        user_playlist = current_user.get_or_create_playlist()
        songs = user_playlist.songs.all()
        return render_template('profile.html', user=current_user, songs=songs)

    @app.route('/share')
    def share():
        return render_template('share.html')

    @app.route('/sign_in', methods=['GET', 'POST'])
    def sign_in():
        if request.method == 'POST':
            username = request.form.get('username')  
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('profile'))

            flash('Invalid username or password', 'error')
            return redirect(url_for('sign_in'))

        return render_template('sign_in.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('sign_in'))
