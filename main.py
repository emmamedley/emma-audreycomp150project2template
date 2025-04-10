from flask import Flask, jsonify, render_template, request, redirect, session, url_for
import random
import os
import requests
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
count = 0

# Spotify API credentials
# You'll need to register your app on the Spotify Developer Dashboard
# and replace these with your own credentials
SPOTIFY_CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"
SPOTIFY_REDIRECT_URI = "http://localhost:5000/callback"  # Change to your actual domain in production
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

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

# Map 8 Ball responses to Spotify mood categories
MOOD_MAPPING = {
    "positive": ["It is certain", "It is decidedly so", "Without a doubt", "Yes definitely", 
                 "You may rely on it", "As I see it, yes", "Most likely", "Outlook good", 
                 "Yes", "Signs point to yes"],
    "uncertain": ["Reply hazy, try again", "Ask again later", "Better not tell you now",
                  "Cannot predict now", "Concentrate and ask again"],
    "negative": ["Don't count on it", "My reply is no", "My sources say no",
                 "Outlook not so good", "Very doubtful"]
}

# Spotify playlist IDs for different moods
SPOTIFY_PLAYLISTS = {
    "positive": "37i9dQZF1DXdPec7aLTmlC",  # Happy Hits playlist
    "uncertain": "37i9dQZF1DWSqmBTGDYngZ",  # Mood Booster playlist
    "negative": "37i9dQZF1DX3YSRoSdA634"    # Life Sucks playlist
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
    # Get a random response
    answer = random.choice(RESPONSES)
    return jsonify({'answer': answer})

# Spotify Authentication Routes
@app.route('/spotify_auth')
def spotify_auth():
    # Generate a random state value for security
    state = str(uuid.uuid4())
    session['spotify_auth_state'] = state
    
    # Parameters for authorization
    auth_params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'state': state,
        'scope': 'user-read-private user-read-email user-modify-playback-state user-read-playback-state'
    }
    
    # Construct auth URL with parameters
    auth_url = 'https://accounts.spotify.com/authorize?' + '&'.join([f"{key}={val}" for key, val in auth_params.items()])
    return jsonify({'auth_url': auth_url})

@app.route('/callback')
def callback():
    # Check state to prevent CSRF attacks
    if request.args.get('state') != session.get('spotify_auth_state'):
        return redirect('/')
    
    # Exchange authorization code for access token
    if 'code' in request.args:
        auth_code = request.args.get('code')
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
        
        response = requests.post('https://accounts.spotify.com/api/token', data=token_data)
        
        if response.status_code == 200:
            token_info = response.json()
            session['spotify_token'] = token_info.get('access_token')
            session['spotify_refresh_token'] = token_info.get('refresh_token')
            session['spotify_token_expiry'] = token_info.get('expires_in')
            
            # Get user profile information
            user_response = requests.get(
                f"{SPOTIFY_API_BASE}/me",
                headers={
                    'Authorization': f"Bearer {session['spotify_token']}"
                }
            )
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                session['spotify_user_name'] = user_info.get('display_name', 'Spotify User')
                session['spotify_user_id'] = user_info.get('id')
    
    return redirect('/')

@app.route('/spotify_status')
def spotify_status():
    if 'spotify_token' in session:
        return jsonify({
            'connected': True,
            'user_name': session.get('spotify_user_name', 'Spotify User')
        })
    else:
        return jsonify({'connected': False})

@app.route('/spotify_disconnect', methods=['POST'])
def spotify_disconnect():
    # Clear Spotify session data
    session.pop('spotify_token', None)
    session.pop('spotify_refresh_token', None)
    session.pop('spotify_token_expiry', None)
    session.pop('spotify_user_name', None)
    session.pop('spotify_user_id', None)
    
    return jsonify({'success': True})

@app.route('/play_spotify_track', methods=['POST'])
def play_spotify_track():
    if 'spotify_token' not in session:
        return jsonify({
            'success': False,
            'message': 'Not connected to Spotify.'
        })
    
    # Get the 8 Ball answer from the request
    answer_text = request.json.get('answer', '')
    
    # Determine the mood based on the answer
    mood = "uncertain"  # Default mood
    for key_word in answer_text.lower():
        if any(response.lower() in answer_text.lower() for response in MOOD_MAPPING["positive"]):
            mood = "positive"
            break
        elif any(response.lower() in answer_text.lower() for response in MOOD_MAPPING["negative"]):
            mood = "negative"
            break
    
    # Get a track from the corresponding playlist
    playlist_id = SPOTIFY_PLAYLISTS[mood]
    
    # Check if user has an active device
    devices_response = requests.get(
        f"{SPOTIFY_API_BASE}/me/player/devices",
        headers={
            'Authorization': f"Bearer {session['spotify_token']}"
        }
    )
    
    if devices_response.status_code != 200 or not devices_response.json().get('devices'):
        return jsonify({
            'success': False,
            'message': 'No active Spotify devices found. Please open Spotify on a device first.'
        })
    
    # Get tracks from the playlist
    playlist_response = requests.get(
        f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks",
        params={
            'limit': 50  # Get up to 50 tracks
        },
        headers={
            'Authorization': f"Bearer {session['spotify_token']}"
        }
    )
    
    if playlist_response.status_code != 200:
        return jsonify({
            'success': False,
            'message': 'Could not get tracks from the playlist.'
        })
    
    tracks = playlist_response.json().get('items', [])
    if not tracks:
        return jsonify({
            'success': False,
            'message': 'No tracks found in the playlist.'
        })
    
    # Select a random track
    track = random.choice(tracks)['track']
    track_uri = track['uri']
    
    # Play the track
    play_response = requests.put(
        f"{SPOTIFY_API_BASE}/me/player/play",
        json={
            'uris': [track_uri]
        },
        headers={
            'Authorization': f"Bearer {session['spotify_token']}"
        }
    )
    
    if play_response.status_code in [200, 204]:
        return jsonify({
            'success': True,
            'track_name': track['name'],
            'artist_name': track['artists'][0]['name']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Could not play the track. Make sure Spotify is open and active.'
        })

# Keep the existing routes for backwards compatibility
@app.route('/increment', methods=['POST'])
def increment():
    global count
    count += 1
    return jsonify({'count': count})

@app.route('/flip_case', methods=['POST'])
def flip_case():
    text = request.json['text']
    flipped_text = ''.join(c.lower() if c.isupper() else c.upper() for c in text)
    return jsonify({'flipped_text': flipped_text})

if __name__ == '__main__':
    app.run(debug=True)
