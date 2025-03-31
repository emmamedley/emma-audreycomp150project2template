const magicBall = document.getElementById('magicBall');
const answerElement = document.getElementById('answer');
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