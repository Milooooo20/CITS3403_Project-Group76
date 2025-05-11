from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

def register_routes(app):
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/compare')
    @login_required
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

            flash('Account created successfully. Please sign in.', 'success')
            return redirect(url_for('sign_in'))

        return render_template('create_account.html')

    @app.route('/edit_playlist')
    def edit_playlist():
        return render_template('edit_playlist.html')

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)

    @app.route('/share', methods=['GET', 'POST'])
    @login_required
    def share():
        if request.method == 'POST':
            user_id = request.form.get('userId')
            user = User.query.get_or_404(user_id)

            if user not in current_user.shared_with:
                current_user.shared_with.append(user)
                db.session.commit()
            
            return jsonify({'success': True}), 200
        
        return render_template('share.html')

    @app.route('/search_users/<username>')
    def search_users(username):
        matching_users = User.query.filter(User.username.ilike(f"%{username}%")).all()
        return jsonify([{'id': user.id, 'username': user.username} for user in matching_users])

    @app.route('/get_shared_users')
    def get_shared_users():
        shared_with = [{'id': user.id, 'username': user.username} for user in current_user.shared_with]
        shared_by = [{'id': user.id, 'username': user.username} for user in current_user.shared_by]
        return jsonify({'shared_with': shared_with, 'shared_by': shared_by})

    @app.route('/unshare/<int:user_id>', methods=['POST'])
    def unshare(user_id):
        user = User.query.get_or_404(user_id)
        if user in current_user.shared_with:
            current_user.shared_with.remove(user)
            db.session.commit()
        return jsonify({'success': True}), 200
    
    @app.route('/sign_in', methods=['GET', 'POST'])
    def sign_in():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
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
