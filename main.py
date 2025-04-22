from flask import Flask, jsonify, render_template, request, redirect, session, url_for
import random
import os
import requests
import base64
import urllib.parse

app = Flask(__name__)

app.secret_key = "your_secret_key_here"


SPOTIFY_CLIENT_ID = "c0f94698a04a46f99e22cda3b8f64029"
SPOTIFY_CLIENT_SECRET = "e3058ec934944a559421b5d6f72f9ede"
SPOTIFY_REDIRECT_URI = "http://localhost:80/spotify-callback"


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


EXPANDED_MOOD_MAPPING = {
   
    "joyful": "happy,feel-good,pop",
    "cheerful": "happy,feel-good,pop",
    "excited": "happy,edm,pop",
    "upbeat": "happy,dance,pop",
    "elated": "happy,uplifting,pop",
    "ecstatic": "happy,edm,festival",
    
   
    "melancholic": "sad,indie,blues",
    "gloomy": "sad,dark,blues",
    "depressed": "sad,emo,indie",
    "sorrowful": "sad,emotional,piano",
    "miserable": "sad,blues,emotional",
    "heartbroken": "sad,breakup,emotional",
    
  
    "furious": "metal,hardcore,punk",
    "irritated": "rock,punk,alt-rock",
    "frustrated": "rock,grunge,alt-rock",
    "outraged": "metal,hardcore,rock",
    "mad": "rock,alt-rock,punk",
    
   
    "calm": "chill,ambient,acoustic",
    "peaceful": "ambient,meditation,acoustic",
    "tranquil": "ambient,piano,classical",
    "serene": "ambient,instrumental,classical",
    "mellow": "chill,lofi,acoustic",
    
  
    "lively": "dance,electronic,pop",
    "vibrant": "dance,pop,edm",
    "dynamic": "electronic,edm,house",
    "pumped": "workout,electronic,hip-hop",
    "active": "workout,electronic,rock",
    
   
    "loving": "romance,r-n-b,soul",
    "passionate": "romance,latin,r-n-b",
    "affectionate": "romance,acoustic,soft-rock",
    "tender": "romance,piano,acoustic",
    "intimate": "romance,jazz,soul",
    
    
    "concentrated": "focus,study,instrumental",
    "determined": "focus,motivational,instrumental",
    "dedicated": "focus,instrumental,classical",
    "attentive": "focus,ambient,instrumental",
    
 
    "sentimental": "oldies,90s,80s",
    "reminiscent": "oldies,70s,60s",
    "retro": "80s,disco,synthwave",
    "vintage": "60s,70s,oldies",
    
  
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

@app.route('/get_random_mood', methods=['GET'])
def get_random_mood():
    all_moods = list(MOOD_GENRES.keys()) + list(EXPANDED_MOOD_MAPPING.keys())
    unique_moods = list(set(all_moods))
    random_mood = random.choice(unique_moods)
    return jsonify({'mood': random_mood})

@app.route('/get_song', methods=['POST'])
def get_song():
    data = request.json
    mood = data.get('mood', '').lower()
    use_personalized = data.get('personalized', True)  
    
   
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
    
  
    if response.status_code == 401:
      
        if refresh_token_if_expired():
           
            headers['Authorization'] = f'Bearer {session["access_token"]}'
            response = requests.get(url, headers=headers, params=params)
        else:
            raise Exception("Spotify session expired. Please reconnect.")
    
    response.raise_for_status()
    return response.json()

def get_personalized_recommendation(mood=None):
    """Get song recommendation based on user's listening history and mood"""
    try:
       
        if not refresh_token_if_expired():
            raise Exception("Failed to refresh token. Please reconnect to Spotify.")
        
      
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
        
        
        seed_genres = []
        if mood:
            genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
            seed_genres = genres.split(',')[:1]  
        
  
        if not seed_tracks and not seed_artists and not seed_genres:
            if mood:
                genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
                return get_spotify_recommendation(genres)
            else:
                return {"name": "No recommendation data available", "artist": "", "url": ""}
        
        
        recommendations_url = 'https://api.spotify.com/v1/recommendations'
        
        headers = {
            'Authorization': f'Bearer {session["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        
        params = {
            'limit': 1
        }
        
        
        if seed_tracks:
            params['seed_tracks'] = ','.join(seed_tracks[:2])
        
        if seed_artists:
           
            remaining_seeds = 5 - len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0)
            if remaining_seeds > 0:
                params['seed_artists'] = ','.join(seed_artists[:remaining_seeds])
        
      
        if seed_genres:
            used_seeds = len(params.get('seed_tracks', '').split(',') if 'seed_tracks' in params else 0)
            used_seeds += len(params.get('seed_artists', '').split(',') if 'seed_artists' in params else 0)
            
            if used_seeds < 5:
                remaining_seeds = 5 - used_seeds
                params['seed_genres'] = ','.join(seed_genres[:remaining_seeds])
        
        
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
        
        
        if response.status_code == 401:
           
            if refresh_token_if_expired():
                
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
        
        print(f"Error getting personalized recommendation: {str(e)}")
        if mood:
            genres = EXPANDED_MOOD_MAPPING.get(mood.lower(), MOOD_GENRES.get(mood.lower(), mood.lower()))
            return get_spotify_recommendation(genres)
        else:
            return {"name": "Error getting recommendation", "artist": "", "url": ""}

def get_spotify_recommendation(genres):
    """Get song recommendation based on genres"""
    if 'access_token' not in session:
        raise Exception("Not authenticated with Spotify")
    
    
    if not refresh_token_if_expired():
        raise Exception("Failed to refresh token. Please reconnect to Spotify.")
    
    recommendations_url = 'https://api.spotify.com/v1/recommendations'
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    
    genre_list = genres.split(',')
    seed_genres = ','.join(genre_list[:5])  
    
    params = {
        'seed_genres': seed_genres,
        'limit': 1  
    }
    
    response = requests.get(recommendations_url, headers=headers, params=params)
    
   
    if response.status_code == 401:
        
        if refresh_token_if_expired():
            
            headers['Authorization'] = f'Bearer {session["access_token"]}'
            response = requests.get(recommendations_url, headers=headers, params=params)
        else:
            raise Exception("Spotify session expired. Please reconnect.")
    
    response.raise_for_status()
    data = response.json()
    
    if not data['tracks']:
        return {"name": "No song found for your mood", "artist": "", "url": ""}
    
    track = data['tracks'][0]
    song_info = {
        "name": track['name'],
        "artist": track['artists'][0]['name'],
        "url": track['external_urls']['spotify'],
        "preview_url": track['preview_url'],
        "album_image": track['album']['images'][0]['url'] if track['album']['images'] else "",
    }
    
    return song_info

@app.route('/spotify-auth')
def spotify_auth():
    auth_url = get_spotify_auth_url()
    return jsonify({'auth_url': auth_url})

@app.route('/spotify-callback')
def spotify_callback():
    code = request.args.get('code')
    
    if code:
        
        try:
            token_data = get_spotify_token(code)
            session['access_token'] = token_data['access_token']
            session['refresh_token'] = token_data.get('refresh_token')
            
            import time
            session['token_expiry'] = int(time.time()) + token_data.get('expires_in', 3600)
            
            return redirect(url_for('index', spotify_connected='true'))
        except Exception as e:
            return redirect(url_for('index', spotify_error=str(e)))
    
    return redirect(url_for('index', spotify_error='Authorization failed'))

def get_spotify_token(code):
    """Exchange authorization code for access token"""
    token_url = 'https://accounts.spotify.com/api/token'
    
  
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

def refresh_token_if_expired():
    """Check if token is expired and refresh if needed"""
    if 'access_token' not in session:
        return False
    
    if 'token_expiry' not in session or 'refresh_token' not in session:
        return False
    
   
    import time
    current_time = int(time.time())
    
    if current_time >= session.get('token_expiry', 0):
        try:
            
            token_url = 'https://accounts.spotify.com/api/token'
            
            
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
            
            
            session['access_token'] = token_data['access_token']
            if 'refresh_token' in token_data:
                session['refresh_token'] = token_data['refresh_token']
            
          
            session['token_expiry'] = int(time.time()) + token_data.get('expires_in', 3600)
            
            return True
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return False
    
    return True

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)