
// const modelViewer = document.getElementById('veux-viewer');
// const toggleButton = document.getElementById('toggle-animation');
// const stepBackwardButton = document.getElementById('step-backward');
// const stepForwardButton = document.getElementById('step-forward');

// toggleButton.addEventListener('click', () => {
//   if (modelViewer.paused) {
//     modelViewer.play();
//     toggleButton.textContent = 'Pause';
//   } else {
//     modelViewer.pause();
//     toggleButton.textContent = 'Play';
//   }
// });

// stepBackwardButton.addEventListener('click', () => {
//   if (modelViewer.currentTime > 0) {
//     modelViewer.currentTime -= 0.1; // Step backward by 0.1 seconds
//   }
// });

// stepForwardButton.addEventListener('click', () => {
//   if (modelViewer.currentTime < modelViewer.totalTime) {
//     modelViewer.currentTime += 0.1; // Step forward by 0.1 seconds
//   }
// });

// // Disable step buttons when out of range
// modelViewer.addEventListener('timeupdate', () => {
//   stepBackwardButton.disabled = modelViewer.currentTime <= 0;
//   stepForwardButton.disabled = modelViewer.currentTime >= modelViewer.totalTime;
// });

class AnimationController {
    constructor(viewerId, toggleId, backId, forwardId) {
        this.modelViewer = document.getElementById(viewerId);
        this.toggleButton = document.getElementById(toggleId);
        this.stepBackwardButton = document.getElementById(backId);
        this.stepForwardButton = document.getElementById(forwardId);

        this._bindEvents();
    }

    _bindEvents() {
        this.toggleButton.addEventListener('click', () => this.togglePlayPause());
        // this.stepBackwardButton.addEventListener('click', () => this.stepBackward());
        // this.stepForwardButton.addEventListener('click', () => this.stepForward());

        // this.modelViewer.addEventListener('timeupdate', () => this.updateStepButtons());
    }

    togglePlayPause() {
        if (this.modelViewer.paused) {
            this.modelViewer.play();
            this.toggleButton.textContent = 'Pause';
        } else {
            this.modelViewer.pause();
            this.toggleButton.textContent = 'Play';
        }
    }

    stepBackward() {
        if (this.modelViewer.currentTime > 0) {
            this.modelViewer.currentTime -= 0.1;
        }
    }

    stepForward() {
        if (this.modelViewer.currentTime < this.modelViewer.totalTime) {
            this.modelViewer.currentTime += 0.1;
        }
    }

    updateStepButtons() {
        this.stepBackwardButton.disabled = this.modelViewer.currentTime <= 0;
        this.stepForwardButton.disabled = this.modelViewer.currentTime >= this.modelViewer.totalTime;
    }
}

// Usage:
const controller = new AnimationController(
    'veux-viewer',
    'toggle-animation',
    'step-backward',
    'step-forward'
);
