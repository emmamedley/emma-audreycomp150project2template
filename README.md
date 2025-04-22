# Magic 8 Ball - Mood Music

A fun web application that combines the classic Magic 8 Ball with music recommendations based on your mood! Shake the virtual Magic 8 Ball to discover your mood, then get a personalized song recommendation from Spotify that matches how you're feeling.

![Magic 8 Ball Mood Music Preview](https://example.com/screenshot.png)

## Features

- **Magic 8 Ball Interface**: Click on the 8 Ball to "shake" it and discover your random mood
- **Custom Mood Input**: Enter your own mood if you prefer to choose
- **Spotify Integration**: Connect your Spotify account for personalized music recommendations
- **Mood-to-Music Mapping**: Extensive mapping of moods to musical genres
- **Personalization**: Toggle between generic or personalized recommendations
- **Preview Playback**: Listen to song previews directly in the app (when available)
- **Visual Effects**: Enjoy particle animations and a space-themed UI

## Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: Spotify Web API
- **Animation**: Canvas API for particle effects

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/magic-8-ball-mood-music.git
   cd magic-8-ball-mood-music
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Spotify Developer credentials:
   - Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create a new application
   - Note your Client ID and Client Secret
   - Add `http://localhost:80/spotify-callback` as a Redirect URI in your app settings

5. Update the Spotify credentials in `main.py`:
   ```python
   SPOTIFY_CLIENT_ID = "your_client_id_here"
   SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
   SPOTIFY_REDIRECT_URI = "http://localhost:80/spotify-callback"
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:80
   ```

3. Connect your Spotify account by clicking the "Connect to Spotify" button

4. Shake the Magic 8 Ball to get a random mood and song recommendation, or enter your own mood in the text field

## Mood Mapping

The application maps moods to music genres using a comprehensive dictionary. Some examples:

- **Happy**: feel-good, pop
- **Sad**: emo, blues
- **Relaxed**: chill, ambient, acoustic
- **Energetic**: dance, electronic
- **Nostalgic**: oldies, 90s, 80s

The expanded mapping includes more specific moods like "melancholic," "ethereal," "groovy," and many more.

## Deployment

To deploy this application to a production environment:

1. Update the `SPOTIFY_REDIRECT_URI` to your production URL
2. Update the same URL in your Spotify Developer Dashboard
3. Set up proper environment variables for sensitive credentials
4. Follow deployment instructions for your chosen hosting platform

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues to improve the application.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [Flask](https://flask.palletsprojects.com/)
- [Axios](https://axios-http.com/)
