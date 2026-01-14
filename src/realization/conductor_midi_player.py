"""
Gesture-controlled MIDI player for figured bass realization.
Integrates conductor beat detection with real-time MIDI playback.
"""

import threading
from typing import List, Optional, Callable
from .generator import Chord
from .midi_communicator import MidiCommunicator


class ConductorMidiPlayer:
    """
    MIDI player controlled by conductor gestures.
    Advances through chord progression on detected beats.
    """
    
    def __init__(
        self,
        chords: List[Chord],
        midi_communicator: Optional[MidiCommunicator] = None,
        velocity_base: int = 80,
        velocity_range: int = 40,
        auto_start: bool = False
    ):
        """
        Initialize conductor-controlled MIDI player.
        
        Args:
            chords: List of chords to play
            midi_communicator: MidiCommunicator instance (created if None)
            velocity_base: Base MIDI velocity
            velocity_range: Range for velocity variation based on dynamics
            auto_start: If True, start playing immediately
        """
        self.chords = chords
        self.velocity_base = velocity_base
        self.velocity_range = velocity_range
        
        # MIDI setup
        self.owns_midi = midi_communicator is None
        self.midi = midi_communicator or MidiCommunicator()
        if self.owns_midi:
            self.midi.open()
        
        # Playback state
        self.current_chord_index = 0
        self.is_playing = auto_start
        self.is_stopped = False
        self.last_beat_time: Optional[float] = None
        
        # Threading for safe state updates
        self._lock = threading.Lock()
        
        # Callbacks
        self.on_chord_change: Optional[Callable[[int, Chord], None]] = None
        self.on_progression_complete: Optional[Callable[[], None]] = None
    
    def on_beat(self, beat_event, dynamics: float = 0.5, articulation: float = 0.5):
        """
        Handle a beat event from the conductor.
        
        Args:
            beat_event: BeatEvent from conductor
            dynamics: Dynamic level (0.0-1.0) affects velocity
            articulation: Articulation (0.0=legato, 1.0=staccato)
        """
        if not self.is_playing or self.is_stopped:
            return
        
        with self._lock:
            # Check if we've reached the end
            if self.current_chord_index >= len(self.chords):
                self.is_playing = False
                if self.on_progression_complete:
                    self.on_progression_complete()
                return
            
            # Get current chord
            chord = self.chords[self.current_chord_index]
            
            # Calculate velocity based on dynamics
            velocity = self._calculate_velocity(dynamics, beat_event.velocity)
            
            # Play the chord
            self.midi.play_chord(chord, velocity=velocity, stop_previous=True)
            
            # Trigger callback
            if self.on_chord_change:
                self.on_chord_change(self.current_chord_index, chord)
            
            # Advance to next chord
            self.current_chord_index += 1
            self.last_beat_time = beat_event.timestamp
    
    def _calculate_velocity(self, dynamics: float, beat_velocity: float) -> int:
        """
        Calculate MIDI velocity from dynamics and beat velocity.
        
        Args:
            dynamics: Dynamic level (0.0-1.0)
            beat_velocity: Velocity from beat detection
            
        Returns:
            MIDI velocity (0-127)
        """
        # Combine dynamics and beat velocity
        # Normalize beat velocity (typical range 0-5)
        normalized_beat_velocity = min(1.0, beat_velocity / 5.0)
        
        # Weight dynamics more heavily
        combined = 0.7 * dynamics + 0.3 * normalized_beat_velocity
        
        # Map to velocity range
        velocity = int(self.velocity_base + (combined * self.velocity_range))
        
        # Clamp to MIDI range
        return max(0, min(127, velocity))
    
    def start(self):
        """Start playback (will advance on beats)."""
        with self._lock:
            self.is_playing = True
            self.is_stopped = False
    
    def pause(self):
        """Pause playback."""
        with self._lock:
            self.is_playing = False
            self.midi.stop_chord()
    
    def resume(self):
        """Resume playback."""
        with self._lock:
            self.is_playing = True
    
    def stop(self):
        """Stop playback and reset to beginning."""
        with self._lock:
            self.is_playing = False
            self.is_stopped = True
            self.current_chord_index = 0
            self.midi.stop_chord()
    
    def reset(self):
        """Reset to beginning without stopping."""
        with self._lock:
            self.current_chord_index = 0
            self.midi.stop_chord()
    
    def seek(self, chord_index: int):
        """
        Jump to a specific chord in the progression.
        
        Args:
            chord_index: Index of chord to jump to
        """
        with self._lock:
            if 0 <= chord_index < len(self.chords):
                self.current_chord_index = chord_index
                self.midi.stop_chord()
    
    def get_progress(self) -> tuple[int, int]:
        """
        Get current playback progress.
        
        Returns:
            Tuple of (current_index, total_chords)
        """
        with self._lock:
            return (self.current_chord_index, len(self.chords))
    
    def is_finished(self) -> bool:
        """Check if progression is complete."""
        with self._lock:
            return self.current_chord_index >= len(self.chords)
    
    def set_instruments(self, instrument_map: dict):
        """
        Set MIDI instruments for voices.
        
        Args:
            instrument_map: Dict mapping voice names to MIDI program numbers
        """
        self.midi.set_instruments(instrument_map)
    
    def cleanup(self):
        """Clean up resources."""
        with self._lock:
            self.midi.stop_chord()
            if self.owns_midi:
                self.midi.close()


class LoopingConductorMidiPlayer(ConductorMidiPlayer):
    """
    Conductor MIDI player that loops the chord progression.
    """
    
    def on_beat(self, beat_event, dynamics: float = 0.5, articulation: float = 0.5):
        """Handle beat with looping behavior."""
        if not self.is_playing or self.is_stopped:
            return
        
        with self._lock:
            # Loop back to start if at end
            if self.current_chord_index >= len(self.chords):
                self.current_chord_index = 0
                if self.on_progression_complete:
                    self.on_progression_complete()
            
            # Get current chord
            chord = self.chords[self.current_chord_index]
            
            # Calculate velocity
            velocity = self._calculate_velocity(dynamics, beat_event.velocity)
            
            # Play the chord
            self.midi.play_chord(chord, velocity=velocity, stop_previous=True)
            
            # Trigger callback
            if self.on_chord_change:
                self.on_chord_change(self.current_chord_index, chord)
            
            # Advance to next chord
            self.current_chord_index += 1
            self.last_beat_time = beat_event.timestamp
