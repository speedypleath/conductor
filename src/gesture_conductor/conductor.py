# src/gesture_conductor/conductor.py
"""High-level conductor gesture analyzer."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .detector import GestureDetector, HandPosition
from .beat_detector import BeatDetector, BeatEvent


@dataclass
class ConductorState:
    """Current state of the conductor."""
    tempo_bpm: Optional[float]
    articulation: float  # 0.0 (legato) to 1.0 (staccato)
    beats_detected: int
    last_beat_timestamp: Optional[float]
    is_conducting: bool
    average_velocity: float


class ConductorGestureAnalyzer:
    """Analyzes conducting gestures and extracts musical parameters."""
    
    def __init__(
        self,
        gesture_detector: Optional[GestureDetector] = None,
        beat_detector: Optional[BeatDetector] = None,
        history_window: float = 2.0
    ):
        """
        Initialize conductor gesture analyzer.
        
        Args:
            gesture_detector: GestureDetector instance (created if None)
            beat_detector: BeatDetector instance (created if None)
            history_window: Time window for analysis in seconds
        """
        self.gesture_detector = gesture_detector or GestureDetector()
        self.beat_detector = beat_detector or BeatDetector()
        self.history_window = history_window
        
        self._last_analysis_time: Optional[float] = None
        self._current_state = ConductorState(
            tempo_bpm=None,
            articulation=0.5,
            beats_detected=0,
            last_beat_timestamp=None,
            is_conducting=False,
            average_velocity=0.0
        )
    
    def analyze_frame(
        self,
        frame,
        timestamp: float
    ) -> tuple[Optional[HandPosition], List[BeatEvent], ConductorState]:
        """
        
        Analyze a single frame and update conductor state.
        
        Args:
            frame: Input BGR image frame
            timestamp: Current timestamp in seconds
            
        Returns:
            Tuple of (HandPosition, List of new BeatEvents, ConductorState)
        """
        # Detect hand position
        position = self.gesture_detector.process_frame(frame, timestamp)
        
        if position is None:
            self._current_state.is_conducting = False
            return None, [], self._current_state
        
        # Get recent position history
        recent_positions = self.gesture_detector.get_position_history(
            window_seconds=self.history_window
        )
        
        # Detect beats from position history
        new_beats = []
        if len(recent_positions) >= 3:
            # Only check for new beats periodically to avoid duplicates
            if self._last_analysis_time is None or \
               (timestamp - self._last_analysis_time) >= 0.05:  # 50ms
                
                all_beats = self.beat_detector.detect_beats(recent_positions)
                
                # Filter to only new beats
                if self._last_analysis_time is not None:
                    new_beats = [
                        beat for beat in all_beats
                        if beat.timestamp > self._last_analysis_time
                    ]
                else:
                    new_beats = all_beats
                
                self._last_analysis_time = timestamp
        
        # Update conductor state
        self._update_state(recent_positions, new_beats, timestamp)
        
        return position, new_beats, self._current_state
    
    def _update_state(
        self,
        positions: List[HandPosition],
        new_beats: List[BeatEvent],
        timestamp: float
    ):
        """Update the current conductor state."""
        # Update beat count
        if new_beats:
            self._current_state.beats_detected += len(new_beats)
            self._current_state.last_beat_timestamp = new_beats[-1].timestamp
        
        # Update tempo
        self._current_state.tempo_bpm = self.beat_detector.get_current_tempo()
        
        # Update articulation
        self._current_state.articulation = self.beat_detector.get_average_articulation()
        
        # Calculate average velocity
        if len(positions) >= 2:
            velocities = []
            for i in range(1, len(positions)):
                dt = positions[i].timestamp - positions[i-1].timestamp
                dy = positions[i].y - positions[i-1].y
                dx = positions[i].x - positions[i-1].x
                
                velocity = ((dx**2 + dy**2)**0.5) / dt
                velocities.append(velocity)
            
            import numpy as np
            self._current_state.average_velocity = float(np.mean(velocities))
        
        # Determine if actively conducting
        self._current_state.is_conducting = (
            len(positions) >= 3 and
            self._current_state.average_velocity > 0.1
        )
    
    def get_state(self) -> ConductorState:
        """Get current conductor state."""
        return self._current_state
    
    def get_musical_parameters(self) -> Dict[str, Any]:
        """
        Get musical parameters suitable for audio synthesis.
        
        Returns:
            Dictionary with musical parameters
        """
        state = self._current_state
        
        # Map articulation to note duration multiplier
        # Lower articulation = longer notes (legato)
        # Higher articulation = shorter notes (staccato)
        note_duration_factor = 1.0 - (state.articulation * 0.7)
        
        # Map articulation to attack time
        # Higher articulation = faster attack
        attack_time = 0.01 + (1.0 - state.articulation) * 0.09  # 10ms to 100ms
        
        # Map articulation to release time
        release_time = 0.05 + (1.0 - state.articulation) * 0.45  # 50ms to 500ms
        
        return {
            'tempo_bpm': state.tempo_bpm,
            'articulation': state.articulation,
            'note_duration_factor': note_duration_factor,
            'attack_time_ms': attack_time * 1000,
            'release_time_ms': release_time * 1000,
            'is_conducting': state.is_conducting,
            'beats_detected': state.beats_detected,
            'velocity': state.average_velocity,
            'dynamics': min(1.0, state.average_velocity * 2.0)  # Map velocity to volume
        }
    
    def reset(self):
        """Reset the analyzer state."""
        self.gesture_detector.clear_history()
        self.beat_detector.clear_history()
        self._last_analysis_time = None
        self._current_state = ConductorState(
            tempo_bpm=None,
            articulation=0.5,
            beats_detected=0,
            last_beat_timestamp=None,
            is_conducting=False,
            average_velocity=0.0
        )
