from flask import Flask, jsonify, render_template, request, redirect, session, url_for
import random
import os
import requests
import base64
import urllib.parse

app = Flask(__name__)
# Set a secret key for sessions - in production use a strong, randomly generated key
app.secret_key = "your_secret_key_here"

# Spotify API credentials - you'll need to replace these with your own
SPOTIFY_CLIENT_ID = "c0f94698a04a46f99e22cda3b8f64029"
SPOTIFY_CLIENT_SECRET = "e3058ec934944a559421b5d6f72f9ede"
SPOTIFY_REDIRECT_URI = "http://localhost:80/spotify-callback"

# List of Magic 8 Ball responses as Python code
RESPONSES = [
    "if question:\n  return True  # It is certain.",
    "result = True  # It is decidedly so.",
    "assert answer == True  # Without a doubt.",
    "return True  # Yes definitely.",
    "confidence = 1.0  # You may rely on it.",
    "if analyze(question):\n  print('Yes')  # As I see it, yes.",
    "probability = random.random()\nif probability > 0.2:\n  return True  # Most likely.",
    "forecast = 'positive'  # Outlook good.",
    "answer = True  # Yes.",
    "indicators = [True, True, False, True]\nif sum(indicators) > len(indicators)/2:\n  return True  # Signs point to yes.",
    "import random\nif random.random() < 0.5:\n  return 'Try again'  # Reply hazy, try again.",
    "# Error: Insufficient data\nraise TimeoutError('Ask again later.')",
    "# TODO: Implement this feature\npass  # Better not tell you now.",
    "try:\n  predict(question)\nexcept FutureUncertainError:\n  pass  # Cannot predict now.",
    "while not clear_thinking:\n  meditate()  # Concentrate and ask again.",
    "assert answer != True  # Don't count on it.",
    "return False  # My reply is no.",
    "survey_results = {'yes': 20, 'no': 80}\n# My sources say no.",
    "forecast = 'negative'  # Outlook not so good.",
    "confidence = 0.1  # Very doubtful."
]

# Dictionary mapping moods to Spotify genres
MOOD_GENRES = {
    "happy": "happy,feel-good,pop",
    "sad": "sad,emo,blues",
    "angry": "metal,hard-rock,punk", 
    "relaxed": "chill,ambient,acoustic",
    "energetic": "dance,electronic,workout",
    "romantic": "romance,r-n-b,soul",
    "focused": "focus,study,instrumental",
    "nostalgic": "oldies,90s,80s"
}

# Expanded mood-genre mappings to handle more adjectives
EXPANDED_MOOD_MAPPING = {
    # Happy-related
    "joyful": "happy,feel-good,pop",
    "cheerful": "happy,feel-good,pop",
    "excited": "happy,edm,pop",
    "upbeat": "happy,dance,pop",
    "elated": "happy,uplifting,pop",
    "ecstatic": "happy,edm,festival",
    
    # Sad-related
    "melancholic": "sad,indie,blues",
    "gloomy": "sad,dark,blues",
    "depressed": "sad,emo,indie",
    "sorrowful": "sad,emotional,piano",
    "miserable": "sad,blues,emotional",
    "heartbroken": "sad,breakup,emotional",
    
    # Angry-related
    "furious": "metal,hardcore,punk",
    "irritated": "rock,punk,alt-rock",
    "frustrated": "rock,grunge,alt-rock",
    "outraged": "metal,hardcore,rock",
    "mad": "rock,alt-rock,punk",
    
    # Relaxed-related
    "calm": "chill,ambient,acoustic",
    "peaceful": "ambient,meditation,acoustic",
    "tranquil": "ambient,piano,classical",
    "serene": "ambient,instrumental,classical",
    "mellow": "chill,lofi,acoustic",
    
    # Energetic-related
    "lively": "dance,electronic,pop",
    "vibrant": "dance,pop,edm",
    "dynamic": "electronic,edm,house",
    "pumped": "workout,electronic,hip-hop",
    "active": "workout,electronic,rock",
    
    # Romantic-related
    "loving": "romance,r-n-b,soul",
    "passionate": "romance,latin,r-n-b",
    "affectionate": "romance,acoustic,soft-rock",
    "tender": "romance,piano,acoustic",
    "intimate": "romance,jazz,soul",
    
    # Focused-related
    "concentrated": "focus,study,instrumental",
    "determined": "focus,motivational,instrumental",
    "dedicated": "focus,instrumental,classical",
    "attentive": "focus,ambient,instrumental",
    
    # Nostalgic-related
    "sentimental": "oldies,90s,80s",
    "reminiscent": "oldies,70s,60s",
    "retro": "80s,disco,synthwave",
    "vintage": "60s,70s,oldies",
    
    # More unique moods
    "dreamy": "dream-pop,ambient,indie",
    "mysterious": "dark-ambient,soundtrack,electronic",
    "whimsical": "indie-pop,folk,quirky",
    "confident": "hip-hop,pop,motivational",
    "anxious": "electronic,experimental,indie",
    "hopeful": "indie,uplifting,folk",
    "rebellious": "punk,rock,grunge",
    "spiritual": "meditation,new-age,world",
    "playful": "indie-pop,quirky,children",
    "bored": "lo-fi,chill,indie",
    "creative": "indie,experimental,jazz",
    "ethereal": "ambient,dream-pop,new-age",
    "sophisticated": "jazz,classical,lounge",
    "epic": "soundtrack,orchestral,cinematic",
    "groovy": "funk,disco,soul",
    "tropical": "reggae,dancehall,tropical-house",
    "winter": "acoustic,piano,ambient",
    "summer": "tropical-house,pop,reggae"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():

    answer = random.choice(RESPONSES)
    return jsonify({'answer': answer})

@app.route('/get_song', methods=['POST'])
def get_song():
    data = request.json
    mood = data.get('mood', '').lower()
    use_personalized = data.get('personalized', True)  # Default to personalized recommendations
    
    # Check if the user is authenticated with Spotify
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated with Spotify', 'auth_url': get_spotify_auth_url()})
    
    try:
        if use_personalized:
            song = get_personalized_recommendation(mood)
        else:
            genres = EXPANDED_MOOD_MAPPING.get(mood, MOOD_GENRES.get(mood, mood))
            song = get_spotify_recommendation(genres)
            
        return jsonify({'song': song})
    except Exception as e:
        return jsonify({'error': str(e)})

def get_user_top_items(item_type, time_range='medium_term', limit=10):
    """
    Get user's top tracks or artists
    item_type: 'tracks' or 'artists'
    time_range: 'short_term' (4 weeks), 'medium_term' (6 months), or 'long_term' (years)
    """
    if 'access_token' not in session:
        raise Exception("Not authenticated with Spotify")
    
    # Refresh token if needed
    if not refresh_token_if_expired():
        raise Exception("Failed to refresh token. Please reconnect to Spotify.")
    
    url = f'https://api.spotify.com/v1/me/top/{item_type}'
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'time_range': time_range,
        'limit': limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    # Check if token expired
    if response.status_code == 401:
        # Try refreshing token once more
        if refresh_token_if_expired():
            # Retry request with new token
            headers['Authorization'] = f'Bearer {session["access_token"]}'
            response = requests.get(url, headers=headers, params=params)
        else:
            raise Exception("Spotify session expired. Please reconnect.")
    
    response.raise_for_status()
    return response.json()

def get_personalized_recommendation(mood=None):
    """Get song recommendation based on user's listening history and mood"""
    try:
        # Refresh token if needed
        if not refresh_token_if_expired():
            raise Exception("Failed to refresh token. Please reconnect to Spotify.")
        
        # First, get user's top tracks and artists
        seed_tracks = []
        seed_artists = []
        
        try:
            top_tracks = get_user_top_items('tracks')
            if top_tracks and 'items' in top_tracks and top_tracks['items']:
                seed_tracks = [track['id'] for track in top_tracks['items'][:2]]
        except Exception as e:
            print(f"Error getting top tracks: {str(e)}")
            
        try:
            top_artists = get_user_top_items('artists')
            if top_artists and 'items' in top_artists and top_artists['items']:
                seed_artists = [artist['id'] for artist in top_artists['items'][:2]]
        except Exception as e:
            print(f"Error getting top artists: {str(e)}")
        
        # Get genres based on mood if provided
        seed_genres = []
        if mood:
            genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
            seed_genres = genres.split(',')[:1]  # Take just the first genre to leave room for tracks and artists
        
        # If we couldn't get any seeds, fall back to non-personalized recommendation
        if not seed_tracks and not seed_artists and not seed_genres:
            if mood:
                genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
                return get_spotify_recommendation(genres)
            else:
                return {"name": "No recommendation data available", "artist": "", "url": ""}
        
        # Build recommendation request
        recommendations_url = 'https://api.spotify.com/v1/recommendations'
        
        headers = {
            'Authorization': f'Bearer {session["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        # We can use up to 5 seed values total (tracks, artists, genres combined)
        params = {
            'limit': 1
        }
        
        # Add available seeds, prioritizing tracks and artists over genres
        if seed_tracks:
            params['seed_tracks'] = ','.join(seed_tracks[:2])
        
        if seed_artists:
            # Limit to leave room for tracks
            remaining_seeds = 5 - len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0)
            if remaining_seeds > 0:
                params['seed_artists'] = ','.join(seed_artists[:remaining_seeds])
        
        # Add genres if we still have room
        if seed_genres:
            used_seeds = len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0)
            used_seeds += len(params.get('seed_artists', '').split(',') if 'seed_artists' in params else 0)
            
            if used_seeds < 5:
                remaining_seeds = 5 - used_seeds
                params['seed_genres'] = ','.join(seed_genres[:remaining_seeds])
        
        # If mood is provided, add audio feature targets
        if mood:
            if mood.lower() in ['happy', 'energetic', 'upbeat', 'lively', 'cheerful', 'excited']:
                params['target_energy'] = 0.8
                params['target_valence'] = 0.7
            elif mood.lower() in ['sad', 'melancholic', 'gloomy', 'depressed', 'sorrowful']:
                params['target_energy'] = 0.4
                params['target_valence'] = 0.3
            elif mood.lower() in ['relaxed', 'calm', 'peaceful', 'tranquil', 'mellow']:
                params['target_energy'] = 0.3
                params['target_tempo'] = 90
            elif mood.lower() in ['angry', 'intense', 'furious', 'outraged']:
                params['target_energy'] = 0.8
                params['target_valence'] = 0.4

        response = requests.get(recommendations_url, headers=headers, params=params)
        
        # Check for token expiration
        if response.status_code == 401:
            # Try refreshing token once more
            if refresh_token_if_expired():
                # Retry request with new token
                headers['Authorization'] = f'Bearer {session["access_token"]}'
                response = requests.get(recommendations_url, headers=headers, params=params)
            else:
                raise Exception("Spotify session expired. Please reconnect.")
                
        response.raise_for_status()
        data = response.json()
        
        if not data['tracks']:
            return {"name": "No song found", "artist": "", "url": ""}
        
        track = data['tracks'][0]
        song_info = {
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "url": track['external_urls']['spotify'],
            "preview_url": track['preview_url'],
            "album_image": track['album']['images'][0]['url'] if track['album']['images'] else "",
        }
        
        return song_info
    
    except Exception as e:
        # Fall back to non-personalized recommendation if there's an error
        print(f"Error getting personalized recommendation: {str(e)}")
        if mood:
            genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
            return get_spotify_recommendation(genres)
        else:
            return {"name": "Error getting recommendation", "artist": "", "url": ""}
    """
    Get user's top tracks or artists
    item_type: 'tracks' or 'artists'
    time_range: 'short_term' (4 weeks), 'medium_term' (6 months), or 'long_term' (years)
    """
    if 'access_token' not in session:
        raise Exception("Not authenticated with Spotify")
    
    url = f'https://api.spotify.com/v1/me/top/{item_type}'
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'time_range': time_range,
        'limit': limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    # Check if token expired
    if response.status_code == 401:
        # Could implement token refresh here
        raise Exception("Spotify session expired. Please reconnect.")
    
    response.raise_for_status()
    return response.json()

def get_personalized_recommendation(mood=None):
    """Get song recommendation based on user's listening history and mood"""
    try:
        # First, get user's top tracks and artists
        top_tracks = get_user_top_items('tracks')
        top_artists = get_user_top_items('artists')
        
        # Extract IDs for the API call
        seed_tracks = [track['id'] for track in top_tracks['items'][:2]]
        seed_artists = [artist['id'] for artist in top_artists['items'][:2]]
        
        # Get genres based on mood if provided
        seed_genres = []
        if mood:
            genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
            seed_genres = genres.split(',')[:1]  # Take just the first genre to leave room for tracks and artists
        
        # Build recommendation request
        recommendations_url = 'https://api.spotify.com/v1/recommendations'
        
        headers = {
            'Authorization': f'Bearer {session["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        # We can use up to 5 seed values total (tracks, artists, genres combined)
        params = {
            'limit': 1
        }
        
        # Add available seeds, prioritizing tracks and artists over genres
        if seed_tracks:
            params['seed_tracks'] = ','.join(seed_tracks[:2])
        
        if seed_artists:
            # Limit to leave room for tracks
            remaining_seeds = 5 - len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0)
            params['seed_artists'] = ','.join(seed_artists[:remaining_seeds])
        
        # Add genres if we still have room
        if seed_genres and len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0) + len(params.get('seed_artists', '').split(',') if 'seed_artists' in params else 0) < 5:
            remaining_seeds = 5 - len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0) - len(params.get('seed_artists', '').split(',') if 'seed_artists' in params else 0)
            params['seed_genres'] = ','.join(seed_genres[:remaining_seeds])
        
        # If mood is provided, add audio feature targets
        if mood:
            if mood.lower() in ['happy', 'energetic', 'upbeat', 'lively']:
                params['target_energy'] = 0.8
                params['target_valence'] = 0.7
            elif mood.lower() in ['sad', 'melancholic', 'gloomy']:
                params['target_energy'] = 0.4
                params['target_valence'] = 0.3
            elif mood.lower() in ['relaxed', 'calm', 'peaceful']:
                params['target_energy'] = 0.3
                params['target_tempo'] = 90
            elif mood.lower() in ['angry', 'intense']:
                params['target_energy'] = 0.8
                params['target_valence'] = 0.4

        response = requests.get(recommendations_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data['tracks']:
            return {"name": "No song found", "artist": "", "url": ""}
        
        track = data['tracks'][0]
        song_info = {
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "url": track['external_urls']['spotify'],
            "preview_url": track['preview_url'],
            "album_image": track['album']['images'][0]['url'] if track['album']['images'] else "",
        }
        
        return song_info
    
    except Exception as e:
        # Fall back to non-personalized recommendation if there's an error
        print(f"Error getting personalized recommendation: {str(e)}")
        return get_spotify_recommendation(mood) if mood else {"name": "Error getting recommendation", "artist": "", "url": ""}

@app.route('/spotify-auth')
def spotify_auth():
    auth_url = get_spotify_auth_url()
    return jsonify({'auth_url': auth_url})

@app.route('/spotify-callback')
def spotify_callback():
    code = request.args.get('code')
    
    if code:
        # Exchange code for access token
        try:
            token_data = get_spotify_token(code)
            session['access_token'] = token_data['access_token']
            session['refresh_token'] = token_data.get('refresh_token')
            session['expires_in'] = token_data.get('expires_in')
            return redirect(url_for('index', spotify_connected='true'))
        except Exception as e:
            return redirect(url_for('index', spotify_error=str(e)))
    
    return redirect(url_for('index', spotify_error='Authorization failed'))
# This function to main.py to handle token refresh

def refresh_token_if_expired():
    """Check if token is expired and refresh if needed"""
    if 'access_token' not in session:
        return False
    
    if 'token_expiry' not in session or 'refresh_token' not in session:
        return False
    
    # Check if token is expired
    import time
    current_time = int(time.time())
    
    if current_time >= session.get('token_expiry', 0):
        try:
            # Token is expired, refresh it
            token_url = 'https://accounts.spotify.com/api/token'
            
            # Encode client ID and secret for Basic Auth
            auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': session['refresh_token']
            }
            
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Update session with new token
            session['access_token'] = token_data['access_token']
            if 'refresh_token' in token_data:
                session['refresh_token'] = token_data['refresh_token']
            
            # Set token expiry time
            session['token_expiry'] = int(time.time()) + token_data.get('expires_in', 3600)
            
            return True
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return False
    
    return True

# Update the get_spotify_auth_url function in main.py

def get_spotify_auth_url():
    """Generate Spotify authorization URL with extended permissions"""
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-read-private user-read-email user-top-read user-read-recently-played',
    }
    
    auth_url = 'https://accounts.spotify.com/authorize?'
    auth_url += urllib.parse.urlencode(params)
    return auth_url