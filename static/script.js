document.addEventListener('DOMContentLoaded', function() {
  const magicBall = document.getElementById('magicBall');
  const answerElement = document.getElementById('answer');
  const moodSelector = document.getElementById('moodSelector');
  const spotifyConnectBtn = document.getElementById('spotifyConnectBtn');
  const spotifyStatus = document.getElementById('spotifyStatus');
  const songRecommendation = document.getElementById('songRecommendation');
  
  // Check if we've just returned from Spotify auth
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('spotify_connected') && urlParams.get('spotify_connected') === 'true') {
    spotifyStatus.textContent = 'Connected to Spotify!';
    spotifyStatus.style.color = '#1DB954';
    spotifyConnectBtn.textContent = 'Reconnect to Spotify';
    
    // Clean the URL without refreshing the page
    window.history.replaceState({}, document.title, '/');
  } else if (urlParams.has('spotify_error')) {
    spotifyStatus.textContent = 'Error connecting to Spotify: ' + urlParams.get('spotify_error');
    spotifyStatus.style.color = 'red';
    
    // Clean the URL without refreshing the page
    window.history.replaceState({}, document.title, '/');
  }
  
  // Connect to Spotify button
  spotifyConnectBtn.addEventListener('click', function() {
    // Get the authentication URL from the server
    axios.get('/spotify-auth')
      .then(function(response) {
        if (response.data.auth_url) {
          // Redirect to Spotify authorization page
          window.location.href = response.data.auth_url;
        }
      })
      .catch(function(error) {
        console.error('Error getting Spotify auth URL:', error);
        spotifyStatus.textContent = 'Error connecting to Spotify';
        spotifyStatus.style.color = 'red';
      });
  });
  
  // Magic 8 Ball click handler
  magicBall.addEventListener('click', function() {
    // Get the selected mood
    const mood = moodSelector.value;
    
    // Visual feedback for the click
    magicBall.style.transform = 'scale(0.95)';
    
    // Reset the answer opacity
    answerElement.style.opacity = 0;
    
    // Hide any previous song recommendation
    songRecommendation.classList.remove('active');
    
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
          
          // Get song recommendation from server
          axios.post('/get_song', { mood: mood })
            .then(function(response) {
              if (response.data.error) {
                // Handle error (like not authenticated)
                answerElement.textContent = "You need to connect to Spotify first!";
                answerElement.style.opacity = 1;
                
                if (response.data.auth_url) {
                  // Prompt to connect
                  spotifyStatus.innerHTML = 'Please <a href="' + response.data.auth_url + '">connect to Spotify</a> to get song recommendations';
                  spotifyStatus.style.color = '#ff9800';
                }
              } else if (response.data.song) {
                // Display the song recommendation
                const song = response.data.song;
                
                // Show the text answer
                answerElement.textContent = `Based on your ${mood} mood, here's a song for you:`;
                answerElement.style.opacity = 1;
                answerElement.classList.add('fade-in');
                
                // Build the song recommendation HTML
                let songHTML = `
                  <img src="${song.album_image}" alt="${song.name} album cover" class="song-cover">
                  <div class="song-title">${song.name}</div>
                  <div class="song-artist">by ${song.artist}</div>
                  <a href="${song.url}" target="_blank" class="spotify-play-button">
                    Play on Spotify
                  </a>
                `;
                
                // Add audio preview if available
                if (song.preview_url) {
                  songHTML += `
                    <div class="preview-player" style="margin-top: 15px;">
                      <audio controls src="${song.preview_url}"></audio>
                    </div>
                  `;
                }
                
                // Display the song recommendation
                songRecommendation.innerHTML = songHTML;
                songRecommendation.classList.add('active');
                
                // Remove the animation class after it completes
                setTimeout(() => {
                  answerElement.classList.remove('fade-in');
                }, 1500);
              }
            })
            .catch(function(error) {
              console.log(error);
              answerElement.textContent = "Error getting your song recommendation. Try again.";
              answerElement.style.opacity = 1;
            });
        }, 500);
      }
    }, 100);
  });
});