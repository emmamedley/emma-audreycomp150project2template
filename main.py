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
SPOTIFY_REDIRECT_URI = "https://yourdomain.com/spotify-callback"

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
    # Get a random response
    answer = random.choice(RESPONSES)
    return jsonify({'answer': answer})

@app.route('/get_song', methods=['POST'])
def get_song():
    data = request.json
    mood = data.get('mood', '').lower()
    
    # Check if the user is authenticated with Spotify
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated with Spotify', 'auth_url': get_spotify_auth_url()})
    
    # Get genres based on mood
    genres = MOOD_GENRES.get(mood, "pop")
    
    # Call Spotify API to get recommendations
    try:
        song = get_spotify_recommendation(genres)
        return jsonify({'song': song})
    except Exception as e:
        return jsonify({'error': str(e)})

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

def get_spotify_auth_url():
    """Generate Spotify authorization URL"""
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': 'user-read-private user-read-email',
    }
    
    auth_url = 'https://accounts.spotify.com/authorize?'
    auth_url += urllib.parse.urlencode(params)
    return auth_url

def get_spotify_token(code):
    """Exchange authorization code for access token"""
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Encode client ID and secret for Basic Auth
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def get_spotify_recommendation(genres):
    """Get song recommendation from Spotify based on genres"""
    if 'access_token' not in session:
        raise Exception("Not authenticated with Spotify")
    
    recommendations_url = 'https://api.spotify.com/v1/recommendations'
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'seed_genres': genres,
        'limit': 1
    }
    
    response = requests.get(recommendations_url, headers=headers, params=params)
    
    # Check if token expired
    if response.status_code == 401:
        # Could implement token refresh here
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

if __name__ == '__main__':
    app.run(debug=True)