
const modelViewer = document.getElementById('veux-viewer');
const toggleButton = document.getElementById('toggle-animation');
const stepBackwardButton = document.getElementById('step-backward');
const stepForwardButton = document.getElementById('step-forward');

toggleButton.addEventListener('click', () => {
  if (modelViewer.paused) {
    modelViewer.play();
    toggleButton.textContent = 'Pause';
  } else {
    modelViewer.pause();
    toggleButton.textContent = 'Play';
  }
});

stepBackwardButton.addEventListener('click', () => {
  if (modelViewer.currentTime > 0) {
    modelViewer.currentTime -= 0.1; // Step backward by 0.1 seconds
  }
});

stepForwardButton.addEventListener('click', () => {
  if (modelViewer.currentTime < modelViewer.totalTime) {
    modelViewer.currentTime += 0.1; // Step forward by 0.1 seconds
  }
});

// Disable step buttons when out of range
modelViewer.addEventListener('timeupdate', () => {
  stepBackwardButton.disabled = modelViewer.currentTime <= 0;
  stepForwardButton.disabled = modelViewer.currentTime >= modelViewer.totalTime;
});

