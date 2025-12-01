```markdown
# Gesture Conductor

A real-time conducting gesture recognition system that detects hand movements and extracts musical parameters like tempo, articulation, and beat timing using computer vision and MediaPipe.

## Installation

### Prerequisites

- Python 3.9 or higher
- Webcam or camera device
- UV package manager (recommended) or pip

### Using UV (Recommended)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/gesture-conductor.git
cd gesture-conductor

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/gesture-conductor.git
cd gesture-conductor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Quick Start

Run the gesture conductor with default settings:

```bash
python -m gesture_conductor.main
```

### Keyboard Controls

- **SPACE**: Toggle beat detection on/off
- **R**: Reset/clear beat history
- **S**: Save current session data
- **Q** or **ESC**: Quit application

## Basic Usage

```python
from gesture_conductor.detector import GestureDetector
from gesture_conductor.beat_detector import BeatDetector

# Initialize components
gesture_detector = GestureDetector()
beat_detector = BeatDetector()

# Process video frame
hands = gesture_detector.detect(frame)

if hands:
    # Detect beats
    beats = beat_detector.detect_beats(
        gesture_detector.get_position_history()
    )
  
    # Get current tempo
    tempo = beat_detector.get_current_tempo()
    print(f"Current tempo: {tempo} BPM")
```

## Project Structure

```
gesture-conductor/
├── gesture_conductor/
│   ├── __init__.py
│   ├── detector.py           # Hand tracking and gesture detection
│   ├── beat_detector.py      # Beat detection and tempo extraction
│   ├── musical_params.py     # Musical parameter extraction
│   ├── visualizer.py         # Real-time visualization
│   └── main.py              # Main application entry point
├── tests/
│   ├── test_detector.py
│   ├── test_beat_detector.py
│   └── test_musical_params.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Development

### Install development dependencies

```bash
uv pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
black gesture_conductor/
ruff check gesture_conductor/
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [MediaPipe](https://mediapipe.dev/) for hand tracking
- Uses [OpenCV](https://opencv.org/) for video processing
```