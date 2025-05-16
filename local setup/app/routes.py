from flask import render_template, request, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Playlist, Song
from app.SpotifyApi import SpotifyAPI
from collections import Counter
from collections import defaultdict
import random
from flask_wtf.csrf import generate_csrf

### HARDCODED CREDENTIALS FOR TESTING ONLY THESE BEING HERE IS A SECURITY RISK AND SHOULD BE FIXED BEFORE FINAL SUBMISSION
spotify_api = SpotifyAPI(
    client_id='246e6eecd23b454ebc4bbe5127e9579c',
    client_secret='a55d3209c220401f9a58683a84e06bf3' 
)

def register_routes(app):
    @app.route('/')
    def home():
        return render_template('home.html', user=current_user)

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

        csrf_token = generate_csrf()
        return render_template('create_account.html', csrf_token=csrf_token)

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
        user_id = request.args.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('share'))
            elif user not in current_user.shared_by:
                flash('You cannot view this user\'s profile', 'error')
                return redirect(url_for('share'))
            is_own_profile = False
        else:
            user = current_user
            is_own_profile = True
        
        user_playlist = user.get_or_create_playlist()
        songs = user_playlist.songs.all()

        artist_counts = Counter()
        genre_counts = Counter()

        all_artists = []

        for song in songs:
            artists = [artist.strip() for artist in song.artist.split(',')]
            artist_counts.update(artists)
            all_artists.extend(artists)

            # Fetch genre via Spotify API
            track_data = spotify_api.get_track(song.spotify_id)
            if track_data.get('artists'):
                first_artist_id = track_data['artists'][0]['id']
                artist_data = spotify_api.get_artist(first_artist_id)
                genres = artist_data.get('genres', [])
                if genres:
                    genre_counts[genres[0]] += 1
                else:
                    genre_counts['Unknown'] += 1

        # Get top 3
        top_genres = [genre for genre, _ in genre_counts.most_common(3)]
        top_artists = [artist for artist, _ in artist_counts.most_common(3)]
        
        if len(all_artists) >= 2:
            random_artists = random.sample(all_artists, 2)
        else:
            random_artists = all_artists

        recommendations = []
        song_ids_in_playlist = {song.spotify_id for song in songs}

        for artist_name in random_artists:
            search_results = spotify_api.search_tracks(artist_name, limit=1)
            if search_results['tracks']['items']:
                artist_id = search_results['tracks']['items'][0]['artists'][0]['id']
                top_tracks = spotify_api.get_tracks_by_artist(artist_id)
                new_songs = [track for track in top_tracks if track['id'] not in song_ids_in_playlist]
                if new_songs:
                    recommendations.append(random.choice(new_songs))

        while len(recommendations) < 2:
            recommendations.append(None)

        
        genre_recommendation = None

        if all_artists:
            random_artist_name = random.choice(all_artists)
            search_result = spotify_api.search_tracks(random_artist_name, limit=5)

            if search_result['tracks']['items']:
                track = random.choice(search_result['tracks']['items'])
                artist_id = track['artists'][0]['id']
                artist_data = spotify_api.get_artist(artist_id)
                genres = artist_data.get('genres', [])

                if genres:
                    genre = random.choice(genres)
                    genre_search = spotify_api.search_tracks(genre, limit=50)

                    if genre_search.get('tracks') and genre_search['tracks'].get('items'):
                        genre_tracks = genre_search['tracks']['items']
                        random.shuffle(genre_tracks)

                        # Try to recommend from a different artist
                        for track in genre_tracks:
                            candidate_artist = track['artists'][0]['name']
                            if candidate_artist not in all_artists and track['id'] not in song_ids_in_playlist:
                                genre_recommendation = track
                                break

                        # Fallback: allow same artist but different song
                        if not genre_recommendation:
                            for track in genre_tracks:
                                if track['id'] not in song_ids_in_playlist:
                                    genre_recommendation = track
                                    break

        return render_template('profile.html',
                            user=user,
                            songs=songs,
                            top_genres=top_genres,
                            top_artists=top_artists,
                            recommended_song_1=recommendations[0],
                            recommended_song_2=recommendations[1],
                            recommended_song_genre=genre_recommendation,
                            is_own_profile=is_own_profile)


    @app.route('/analysis')
    @login_required
    def analysis():
        user_id = request.args.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('share'))
            elif user not in current_user.shared_by:
                flash('You cannot view this user\'s analysis', 'error')
                return redirect(url_for('share'))
        else:
            user = current_user
        
        user_playlist = user.get_or_create_playlist()
        songs = user_playlist.songs.all()

        total_duration = 0  # To accumulate the total song length in milliseconds
        artist_durations = {}  # Dictionary to store the total duration per artist
        genre_durations = defaultdict(int)  # To store total duration per genre
        num_songs = len(songs)  # Total number of songs
        longest_song = None
        longest_duration = 0  # Track the longest song duration

        artist_counts = Counter()  # To count artist occurrences
        genre_counts = Counter()  # To count songs per genre
        genre_to_songs = defaultdict(list)  # Group songs by genre

        for song in songs:
            # Split by comma and count individual artists
            artists = [artist.strip() for artist in song.artist.split(',')]

            # Fetch track details from Spotify API to get the duration
            track_data = spotify_api.get_track(song.spotify_id)
            duration_ms = track_data.get('duration_ms', 0)  # Duration in milliseconds
            total_duration += duration_ms  # Add to total duration

            # Update the artist-specific duration
            for artist in artists:
                if artist not in artist_durations:
                    artist_durations[artist] = 0
                artist_durations[artist] += duration_ms  # Add the song's duration to the artist's total

            # Update the longest song if this one is longer
            if duration_ms > longest_duration:
                longest_duration = duration_ms
                longest_song = song

            # Count artist occurrences
            artist_counts.update(artists)

            # Fetch genre of the first artist
            if track_data.get('artists'):
                first_artist_id = track_data['artists'][0]['id']
                artist_data = spotify_api.get_artist(first_artist_id)
                genres = artist_data.get('genres', [])
                if genres:
                    genre = genres[0]  # Use the first genre
                else:
                    genre = "Unknown"  # Assign a default genre
                genre_to_songs[genre].append({'title': song.title, 'artist': song.artist})  # Add title and artist
                genre_counts[genre] += 1
                genre_durations[genre] += duration_ms

        # Calculate average song duration in minutes and seconds
        if num_songs > 0:
            avg_duration_ms = total_duration / num_songs
            avg_minutes = avg_duration_ms // 60000  # Convert to minutes
            avg_seconds = (avg_duration_ms % 60000) // 1000  # Get remaining seconds
            avg_duration = f"{int(avg_minutes)}m {int(avg_seconds)}s"
        else:
            avg_duration = "N/A"  # Handle case where there are no songs

        # Convert total duration to minutes and seconds
        total_minutes = total_duration // 60000
        total_seconds = (total_duration % 60000) // 1000
        total_duration_str = f"{total_minutes}m {total_seconds}s"  # Format total duration

        # Find the top song (longest duration)
        if longest_song:
            longest_song_length = f"{longest_duration // 60000}m {(longest_duration % 60000) // 1000}s"
        else:
            longest_song_length = "N/A"

        # Prepare artist counts data for the bar chart
        sorted_artist_counts = sorted(list(artist_counts.items()), key=lambda x: x[1], reverse=True)
        artist_count_labels, artist_count_values = zip(*sorted_artist_counts) if sorted_artist_counts else ([], [])

        # Prepare artist duration data for the pie chart
        sorted_artist_durations = sorted(list(artist_durations.items()), key=lambda x: x[1], reverse=True)
        artist_duration_labels, artist_duration_values = zip(*sorted_artist_durations) if sorted_artist_durations else ([], [])
        artist_duration_values = [duration // 60000 for duration in artist_duration_values]  # Convert duration to minutes

        # Prepare genre counts data for the bar chart
        sorted_genre_counts = sorted(list(genre_counts.items()), key=lambda x: x[1], reverse=True)
        genre_count_labels, genre_count_values = zip(*sorted_genre_counts) if sorted_genre_counts else ([], [])

        # Prepare genre duration data for the pie chart
        sorted_genre_durations = sorted(list(genre_durations.items()), key=lambda x: x[1], reverse=True)
        genre_duration_labels, genre_duration_values = zip(*sorted_genre_durations) if sorted_genre_durations else ([], [])
        genre_duration_values = [duration // 60000 for duration in genre_duration_values]  # Convert to minutes

        return render_template('analysis.html', 
                            user=user, 
                            artist_count_labels=artist_count_labels, 
                            artist_count_values=artist_count_values, 
                            avg_duration=avg_duration, 
                            longest_song_length=longest_song_length, 
                            total_duration=total_duration_str,
                            num_songs=num_songs,
                            artist_duration_labels=artist_duration_labels,  
                            artist_duration_values=artist_duration_values,  
                            genre_count_labels=genre_count_labels,  
                            genre_count_values=genre_count_values, 
                            genre_duration_labels=genre_duration_labels,
                            genre_duration_values=genre_duration_values,
                            genre_song_titles=genre_to_songs)  
        
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
        
        csrf_token = generate_csrf()
        return render_template('share.html', csrf_token=csrf_token)

    @app.route('/search_users/<username>')
    @login_required
    def search_users(username):
        matching_users = User.query.filter(User.username.ilike(f"%{username}%")).all()
        return jsonify([{'id': user.id, 'username': user.username} for user in matching_users])

    @app.route('/get_shared_users')
    @login_required
    def get_shared_users():
        shared_with = [{'id': user.id, 'username': user.username} for user in current_user.shared_with]
        shared_by = [{'id': user.id, 'username': user.username} for user in current_user.shared_by]
        return jsonify({'shared_with': shared_with, 'shared_by': shared_by})

    @app.route('/unshare', methods=['POST'])
    @login_required
    def unshare():
        user_id = request.form.get('userId')
        user = User.query.get_or_404(user_id)
        
        if user in current_user.shared_with:
            current_user.shared_with.remove(user)
            db.session.commit()
        
        
        return jsonify({'success': True}), 200
    
    @app.route('/sign_in', methods=['GET', 'POST'])
    def sign_in():
        if request.method == 'POST':
            username = request.form.get('username')  
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('profile'))

            flash('Invalid username or password', 'error')
            return redirect(url_for('sign_in'))

        csrf_token = generate_csrf()
        return render_template('sign_in.html', csrf_token=csrf_token)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('sign_in'))
