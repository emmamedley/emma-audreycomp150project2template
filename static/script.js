document.addEventListener('DOMContentLoaded', function() {
  const magicBall = document.getElementById('magicBall');
  const answerElement = document.getElementById('answer');
  const moodSelector = document.getElementById('moodSelector');
  const customAdjective = document.getElementById('customAdjective');
  const customMoodBtn = document.getElementById('customMoodBtn');
  const spotifyConnectBtn = document.getElementById('spotifyConnectBtn');
  const spotifyStatus = document.getElementById('spotifyStatus');
  const songRecommendation = document.getElementById('songRecommendation');

  // Star explosion animation setup
  const canvas = document.getElementById('explosionCanvas');
  const ctx = canvas.getContext('2d');
  let stars = [];

  // Set canvas to full window size
  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Star class for explosion effect
  class Star {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.size = Math.random() * 3 + 1;
      this.speedX = Math.random() * 6 - 3;
      this.speedY = Math.random() * 6 - 3;
      this.color = `hsl(${Math.random() * 60 + 200}, 100%, 50%)`;
      this.life = 1; // Full life
      this.decay = Math.random() * 0.02 + 0.02; // Rate of fading
    }
    
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      this.life -= this.decay;
      
      // Add gravity effect
      this.speedY += 0.05;
    }
    
    draw() {
      ctx.fillStyle = this.color;
      ctx.globalAlpha = this.life;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // Create a star explosion at coordinates
  function createExplosion(x, y) {
    const starCount = 100; // Number of stars in explosion
    for (let i = 0; i < starCount; i++) {
      stars.push(new Star(x, y));
    }
  }

  // Animation loop
  function animate() {
    if (stars.length > 0) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      for (let i = stars.length - 1; i >= 0; i--) {
        stars[i].update();
        stars[i].draw();
        
        // Remove dead stars
        if (stars[i].life <= 0) {
          stars.splice(i, 1);
        }
      }
      
      requestAnimationFrame(animate);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
  
  // Function to get song recommendation based on mood
  function getSongRecommendation(mood) {
    // Reset the answer opacity
    answerElement.style.opacity = 0;
    
    // Hide any previous song recommendation
    songRecommendation.classList.remove('active');
    
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
          answerElement.textContent = `Based on your "${mood}" mood, here's a song for you:`;
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
  }
  
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
    
    // Calculate the 8 ball position for explosion center
    const ballRect = magicBall.getBoundingClientRect();
    const explosionX = ballRect.left + ballRect.width / 2;
    const explosionY = ballRect.top + ballRect.height / 2;
    
    // Create star explosion
    createExplosion(explosionX, explosionY);
    animate();
    
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
          
          // Get song recommendation
          getSongRecommendation(mood);
        }, 500);
      }
    }, 100);
  });

  // Custom mood button click handler
  customMoodBtn.addEventListener('click', function() {
    const customMood = customAdjective.value.trim();
    
    if (customMood) {
      // Small button animation
      customMoodBtn.style.transform = 'scale(0.95)';
      setTimeout(() => {
        customMoodBtn.style.transform = 'scale(1)';
      }, 200);
      
      // Create a small explosion near the button
      const btnRect = customMoodBtn.getBoundingClientRect();
      const explosionX = btnRect.left + btnRect.width / 2;
      const explosionY = btnRect.top + btnRect.height / 2;
      
      // Create star explosion with fewer stars
      const starCount = 30;
      for (let i = 0; i < starCount; i++) {
        stars.push(new Star(explosionX, explosionY));
      }
      animate();
      
      // Get song recommendation
      getSongRecommendation(customMood);
    } else {
      // Provide feedback if input is empty
      answerElement.textContent = "Please enter an adjective first!";
      answerElement.style.opacity = 1;
      
      // Shake the input field to indicate it needs attention
      customAdjective.style.border = '1px solid red';
      setTimeout(() => {
        customAdjective.style.border = '1px solid #ccc';
      }, 2000);
    }
  });
  
  // Enter key press in custom adjective input
  customAdjective.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      customMoodBtn.click();
    }
  });
});
