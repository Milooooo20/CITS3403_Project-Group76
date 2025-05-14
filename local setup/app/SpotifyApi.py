import os
import requests
import base64
import time
from datetime import datetime, timedelta

class SpotifyAPI:
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = datetime.now()

        self.track_cache = {}
        self.artist_cache = {}
    
    def get_token(self):
        if self.token and datetime.now() < self.token_expiry:
            return self.token
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception(f"Token request failed with status {response.status_code}: {response.text}")
        
        json_response = response.json()
        self.token = json_response["access_token"]
        
        expires_in = json_response.get("expires_in", 3600) - 60
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        return self.token
    
    def search_tracks(self, query, limit=10):
        """Search for tracks using the Spotify API"""
        token = self.get_token()
        url = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "q": query,
            "type": "track",
            "limit": limit
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Search request failed with status {response.status_code}: {response.text}")
        
        return response.json()
    
    def get_track(self, track_id):
        """Get details for a specific track"""
        if track_id in self.track_cache:
            return self.track_cache[track_id]

        token = self.get_token()
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limited on get_track. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return self.get_track(track_id)
        elif response.status_code != 200:
            raise Exception(f"Track request failed with status {response.status_code}: {response.text}")

        track_data = response.json()
        self.track_cache[track_id] = track_data
        return track_data

    def get_artist(self, artist_id):
        """Get details for a specific artist"""
        if artist_id in self.artist_cache:
            return self.artist_cache[artist_id]

        token = self.get_token()
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limited on get_artist. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return self.get_artist(artist_id)
        elif response.status_code != 200:
            raise Exception(f"Artist request failed with status {response.status_code}: {response.text}")

        artist_data = response.json()
        self.artist_cache[artist_id] = artist_data
        return artist_data

    def get_tracks_by_artist(self, artist_name, limit=50):
        """Get top tracks for a given artist ID"""
        token = self.get_token()
        url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "market": "US"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limited on get_tracks_by_artist. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return self.get_tracks_by_artist(artist_id)
        elif response.status_code != 200:
            raise Exception(f"Track request failed with status {response.status_code}: {response.text}")

        return response.json().get('tracks', [])
