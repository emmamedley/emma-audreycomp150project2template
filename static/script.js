// Global variables
let stars = [];
let ctx;
let canvas;
let shakeCount = 0;
let maxShakes = 5;
let shakeInterval;

class Star {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.size = Math.random() * 3 + 1;
    this.speedX = Math.random() * 6 - 3;
    this.speedY = Math.random() * 6 - 3;
    this.color = `hsl(${Math.random() * 60 + 200}, 100%, 50%)`;
    this.life = 1;
    this.decay = Math.random() * 0.02 + 0.02;
  }

  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    this.life -= this.decay;
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

// Functions that need to be globally accessible
function createExplosion(x, y) {
  const starCount = 100;
  for (let i = 0; i < starCount; i++) {
    stars.push(new Star(x, y));
  }
}

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

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function getRandomMood() {
  const answerElement = document.getElementById('answer');
  const moodResultElement = document.getElementById('moodResult');
  const songRecommendation = document.getElementById('songRecommendation');

  answerElement.style.opacity = 0;
  moodResultElement.innerHTML = "";
  moodResultElement.classList.remove('active');
  songRecommendation.classList.remove('active');

  axios.get('/get_random_mood')
      .then(function(response) {
        if (response.data.mood) {
          const mood = response.data.mood;

          moodResultElement.textContent = `Your mood: ${mood.charAt(0).toUpperCase() + mood.slice(1)}`;
          moodResultElement.classList.add('active');

          answerElement.textContent = "Now getting a song recommendation for your mood...";
          answerElement.style.opacity = 1;

          getSongRecommendation(mood);
        }
      })
      .catch(function(error) {
        console.log(error);
        answerElement.textContent = "Error getting your mood. Try again.";
        answerElement.style.opacity = 1;
      });
}

function getSongRecommendation(mood) {
  const answerElement = document.getElementById('answer');
  const songRecommendation = document.getElementById('songRecommendation');
  const spotifyStatus = document.getElementById('spotifyStatus');

  const usePersonalized = document.getElementById('personalizedToggle').checked;

  axios.post('/get_song', {
    mood: mood,
    personalized: usePersonalized
  })
      .then(function(response) {
        if (response.data.error) {
          answerElement.textContent = "You need to connect to Spotify first!";
          answerElement.style.opacity = 1;

          if (response.data.auth_url) {
            spotifyStatus.innerHTML = 'Please <a href="' + response.data.auth_url + '">connect to Spotify</a> to get song recommendations';
            spotifyStatus.style.color = '#ff9800';
          }
        } else if (response.data.song) {
          const song = response.data.song;

          const personalizedText = usePersonalized ? " (personalized)" : "";
          answerElement.textContent = `Based on your "${mood}" mood${personalizedText}, here's a song for you:`;
          answerElement.style.opacity = 1;
          answerElement.classList.add('fade-in');

          let songHTML = `
          <img src="${song.album_image}" alt="${song.name} album cover" class="song-cover">
          <div class="song-title">${song.name}</div>
          <div class="song-artist">by ${song.artist}</div>
          <a href="${song.url}" target="_blank" class="spotify-play-button">
            Play on Spotify
          </a>
        `;

          if (song.preview_url) {
            songHTML += `
            <div class="preview-player" style="margin-top: 15px;">
              <audio controls src="${song.preview_url}"></audio>
            </div>
          `;
          }

          songRecommendation.innerHTML = songHTML;
          songRecommendation.classList.add('active');

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

function createStars() {
  const colors = ['pink', 'yellow', 'blue'];
  const numStars = 100;

  for (let i = 0; i < numStars; i++) {
    const star = document.createElement('div');
    star.classList.add('star');
    star.classList.add(colors[Math.floor(Math.random() * colors.length)]);

    star.style.left = `${Math.random() * 100}vw`;
    star.style.top = `${Math.random() * 100}vh`;

    const size = Math.random() * 4 + 1;
    star.style.width = `${size}px`;
    star.style.height = `${size}px`;

    star.style.animationDelay = `${Math.random() * 4}s`;

    document.body.appendChild(star);
  }
}

// DOM Content Loaded event listener
document.addEventListener('DOMContentLoaded', function() {
  const magicBall = document.getElementById('magicBall');
  const answerElement = document.getElementById('answer');
  const moodResultElement = document.getElementById('moodResult');
  const customAdjective = document.getElementById('customAdjective');
  const customMoodBtn = document.getElementById('customMoodBtn');
  const spotifyConnectBtn = document.getElementById('spotifyConnectBtn');
  const spotifyStatus = document.getElementById('spotifyStatus');
  const songRecommendation = document.getElementById('songRecommendation');

  // Initialize canvas and context
  canvas = document.getElementById('explosionCanvas');
  ctx = canvas.getContext('2d');

  // Create stars
  createStars();

  // Set up canvas
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Check Spotify connection from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('spotify_connected') && urlParams.get('spotify_connected') === 'true') {
    spotifyStatus.textContent = 'Connected to Spotify!';
    spotifyStatus.style.color = '#1DB954';
    spotifyConnectBtn.textContent = 'Reconnect to Spotify';

    window.history.replaceState({}, document.title, '/');
  } else if (urlParams.has('spotify_error')) {
    spotifyStatus.textContent = 'Error connecting to Spotify: ' + urlParams.get('spotify_error');
    spotifyStatus.style.color = 'red';

    window.history.replaceState({}, document.title, '/');
  }

  // Spotify connect button event listener
  spotifyConnectBtn.addEventListener('click', function() {
    axios.get('/spotify-auth')
        .then(function(response) {
          if (response.data.auth_url) {
            window.location.href = response.data.auth_url;
          }
        })
        .catch(function(error) {
          console.error('Error getting Spotify auth URL:', error);
          spotifyStatus.textContent = 'Error connecting to Spotify';
          spotifyStatus.style.color = 'red';
        });
  });

  // Magic Ball click event listener
  magicBall.addEventListener('click', function() {
    document.getElementById('ballEight').classList.add('animating-eight');

    magicBall.style.transform = 'scale(0.95)';

    const ballRect = magicBall.getBoundingClientRect();
    const explosionX = ballRect.left + ballRect.width / 2;
    const explosionY = ballRect.top + ballRect.height / 2;

    createExplosion(explosionX, explosionY);
    animate();

    shakeCount = 0;
    maxShakes = 5;

    shakeInterval = setInterval(() => {
      magicBall.style.transform = `scale(0.95) translate(${Math.random() * 10 - 5}px, ${Math.random() * 10 - 5}px)`;
      shakeCount++;

      if (shakeCount >= maxShakes) {
        clearInterval(shakeInterval);

        setTimeout(() => {
          magicBall.style.transform = 'scale(1)';

          getRandomMood();

          // Remove the animation class after a delay
          setTimeout(() => {
            document.getElementById('ballEight').classList.remove('animating-eight');
          }, 1000);
        }, 500);
      }
    }, 100);
  });

  // Custom mood button event listener
  customMoodBtn.addEventListener('click', function() {
    const customMood = customAdjective.value.trim();

    if (customMood) {
      customMoodBtn.style.transform = 'scale(0.95)';
      setTimeout(() => {
        customMoodBtn.style.transform = 'scale(1)';
      }, 200);

      const btnRect = customMoodBtn.getBoundingClientRect();
      const explosionX = btnRect.left + btnRect.width / 2;
      const explosionY = btnRect.top + btnRect.height / 2;

      const starCount = 30;
      for (let i = 0; i < starCount; i++) {
        stars.push(new Star(explosionX, explosionY));
      }
      animate();

      moodResultElement.innerHTML = "";
      moodResultElement.classList.remove('active');

      getSongRecommendation(customMood);
    } else {
      answerElement.textContent = "Please enter a mood first!";
      answerElement.style.opacity = 1;

      customAdjective.style.border = '1px solid red';
      setTimeout(() => {
        customAdjective.style.border = '1px solid #ccc';
      }, 2000);
    }
  });

  // Custom adjective keypress event listener
  customAdjective.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      customMoodBtn.click();
    }
  });
});