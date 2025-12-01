# src/gesture_conductor/__init__.py
"""Gesture Conductor - Audio conducting gesture detection using MediaPipe."""

from .detector import GestureDetector
from .conductor import ConductorGestureAnalyzer
from .beat_detector import BeatDetector

__version__ = "0.1.0"
__all__ = ["GestureDetector", "ConductorGestureAnalyzer", "BeatDetector"]
