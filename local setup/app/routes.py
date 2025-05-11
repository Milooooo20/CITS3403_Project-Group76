from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Playlist, Song
from app.SpotifyApi import SpotifyAPI

### HARDCODED CREDENTIALS FOR TESTING ONLY THESE BEING HERE IS A SECURITY RISK AND SHOULD BE FIXED BEFORE FINAL SUBMISSION
spotify_api = SpotifyAPI(
    client_id='246e6eecd23b454ebc4bbe5127e9579c',
    client_secret='a55d3209c220401f9a58683a84e06bf3' 
)

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
    @login_required
    def edit_playlist():
        user_playlist = current_user.get_or_create_playlist()
        songs = user_playlist.songs.all()
        return render_template('edit_playlist.html', songs=songs)
    
    @app.route('/search_songs')
    @login_required
    def search_songs():
        query = request.args.get('query', '')
        if not query:
            return jsonify([])
        
        try:
            search_results = spotify_api.search_tracks(query)
            tracks = search_results.get('tracks', {}).get('items', [])
            
            formatted_tracks = []
            for track in tracks:
                # Extract the relevant information from each track
                album_art = None
                if track.get('album', {}).get('images'):
                    # Get the smallest image to use as thumbnail
                    images = sorted(track['album']['images'], key=lambda x: x.get('width', 0))
                    if images:
                        album_art = images[0]['url']
                
                formatted_track = {
                    'spotify_id': track['id'],
                    'title': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                    'album': track.get('album', {}).get('name'),
                    'album_art': album_art,
                    'preview_url': track.get('preview_url')
                }
                formatted_tracks.append(formatted_track)
            
            return jsonify(formatted_tracks)
        except Exception as e:
            app.logger.error(f"Error searching Spotify: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/add_song', methods=['POST'])
    @login_required
    def add_song():
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Get the current user's playlist
        user_playlist = current_user.get_or_create_playlist()
        
        # Check if song already exists in playlist
        existing_song = Song.query.filter_by(
            playlist_id=user_playlist.id, 
            spotify_id=data.get('spotify_id')
        ).first()
        
        if existing_song:
            return jsonify({
                'success': False, 
                'message': 'This song is already in your playlist'
            }), 400
        
        # Create new song
        new_song = Song(
            spotify_id=data.get('spotify_id'),
            title=data.get('title'),
            artist=data.get('artist'),
            album=data.get('album'),
            album_art=data.get('album_art'),
            preview_url=data.get('preview_url'),
            playlist_id=user_playlist.id
        )
        
        # Add to database
        db.session.add(new_song)
        db.session.commit()
        
        # Return success with the song object (including its new ID)
        return jsonify({
            'success': True,
            'message': 'Song added to playlist',
            'song': {
                'id': new_song.id,
                'spotify_id': new_song.spotify_id,
                'title': new_song.title,
                'artist': new_song.artist,
                'album': new_song.album,
                'album_art': new_song.album_art,
                'preview_url': new_song.preview_url
            }
        })
    
    @app.route('/delete_song/<int:song_id>', methods=['DELETE'])
    @login_required
    def delete_song(song_id):
        # Get the song and verify it belongs to the current user
        song = Song.query.get_or_404(song_id)
        user_playlist = current_user.get_or_create_playlist()
        
        if song.playlist_id != user_playlist.id:
            return jsonify({
                'success': False,
                'message': 'You do not have permission to delete this song'
            }), 403
        
        # Delete the song
        db.session.delete(song)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Song removed from playlist'
        })
        

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
    
    
