const magicBall = document.getElementById('magicBall');
const answerElement = document.getElementById('answer');
const spotifyButton = document.getElementById('spotifyButton');
const spotifyStatus = document.getElementById('spotifyStatus');

// Magic 8 Ball click functionality
magicBall.addEventListener('click', function() {
  // Visual feedback for the click
  magicBall.style.transform = 'scale(0.95)';
  // Reset the answer opacity
  answerElement.style.opacity = 0;
  // Shake animation
  let shakeCount = 0;
  const maxShakes = 5;
  const shakeInterval = setInterval(() => {
    magicBall.style.transform = `scale(0.95) translate(${Math.random() * 10 - 5}px, ${Math.random() * 10 - 5}px)`;
    shakeCount++;
    if (shakeCount >= maxShakes) {
      clearInterval(shakeInterval);
      
      // Return to normal position after shaking
      setTimeout(() => {
        magicBall.style.transform = 'scale(1)';
        
        // Get answer from server
        axios.post('/get_answer')
          .then(function(response) {
            // Display the answer with fade-in effect
            answerElement.textContent = response.data.answer;
            answerElement.style.opacity = 1;
            answerElement.classList.add('fade-in');
            
            // Remove the animation class after it completes
            setTimeout(() => {
              answerElement.classList.remove('fade-in');
            }, 1500);
            
            // If connected to Spotify, play a corresponding song
            if (localStorage.getItem('spotifyConnected') === 'true') {
              playSpotifyTrack();
            }
          })
          .catch(function(error) {
            console.log(error);
            answerElement.textContent = "Error getting your answer. Try again.";
            answerElement.style.opacity = 1;
          });
      }, 500);
    }
  }, 100);
});

// Spotify connection functionality
spotifyButton.addEventListener('click', function() {
  if (localStorage.getItem('spotifyConnected') === 'true') {
    // Disconnect from Spotify
    disconnectSpotify();
  } else {
    // Connect to Spotify
    connectToSpotify();
  }
});

// Check Spotify connection status on page load
document.addEventListener('DOMContentLoaded', function() {
  updateSpotifyConnectionStatus();
});

function connectToSpotify() {
  axios.get('/spotify_auth')
    .then(function(response) {
      // Redirect to Spotify authorization page
      window.location.href = response.data.auth_url;
    })
    .catch(function(error) {
      console.log(error);
      spotifyStatus.textContent = "Error connecting to Spotify.";
    });
}

function disconnectSpotify() {
  // Clear Spotify tokens
  axios.post('/spotify_disconnect')
    .then(function(response) {
      localStorage.removeItem('spotifyConnected');
      updateSpotifyConnectionStatus();
      spotifyStatus.textContent = "Disconnected from Spotify.";
    })
    .catch(function(error) {
      console.log(error);
      spotifyStatus.textContent = "Error disconnecting from Spotify.";
    });
}

function updateSpotifyConnectionStatus() {
  // Check if connected to Spotify
  axios.get('/spotify_status')
    .then(function(response) {
      if (response.data.connected) {
        localStorage.setItem('spotifyConnected', 'true');
        spotifyButton.textContent = 'Disconnect from Spotify';
        spotifyStatus.textContent = `Connected as: ${response.data.user_name}`;
      } else {
        localStorage.removeItem('spotifyConnected');
        spotifyButton.innerHTML = '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png" alt="Spotify Logo" class="spotify-logo">Connect to Spotify';
        spotifyStatus.textContent = '';
      }
    })
    .catch(function(error) {
      console.log(error);
      localStorage.removeItem('spotifyConnected');
      spotifyButton.innerHTML = '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png" alt="Spotify Logo" class="spotify-logo">Connect to Spotify';
    });
}

function playSpotifyTrack() {
  // Get the current 8 ball response
  const currentAnswer = answerElement.textContent;
  
  // Request server to play a song based on the 8 ball response
  axios.post('/play_spotify_track', { answer: currentAnswer })
    .then(function(response) {
      if (response.data.success) {
        spotifyStatus.textContent = `Now playing: ${response.data.track_name} by ${response.data.artist_name}`;
      } else {
        spotifyStatus.textContent = response.data.message || "Couldn't play a track.";
      }
    })
    .catch(function(error) {
      console.log(error);
      spotifyStatus.textContent = "Error playing Spotify track.";
    });
}
