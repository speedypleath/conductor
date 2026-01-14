"""
Tempo-adaptive MIDI player for figured bass realization.
Continuously adapts playback speed to match conductor's tempo.
"""

import threading
import time
from typing import List, Optional, Callable
from .generator import Chord
from .midi_communicator import MidiCommunicator


class AdaptiveMidiPlayer:
    """
    MIDI player that adapts to conductor's tempo in real-time.
    Plays through chord progression at the conductor's detected tempo.
    """
    
    def __init__(
        self,
        chords: List[Chord],
        midi_communicator: Optional[MidiCommunicator] = None,
        velocity_base: int = 80,
        velocity_range: int = 40,
        default_bpm: float = 120.0,
        loop: bool = True
    ):
        """
        Initialize tempo-adaptive MIDI player.
        
        Args:
            chords: List of chords to play
            midi_communicator: MidiCommunicator instance (created if None)
            velocity_base: Base MIDI velocity
            velocity_range: Range for velocity variation based on dynamics
            default_bpm: Default tempo when no conductor tempo detected
            loop: If True, loop the progression
        """
        self.chords = chords
        self.velocity_base = velocity_base
        self.velocity_range = velocity_range
        self.default_bpm = default_bpm
        self.loop = loop
        
        # MIDI setup
        self.owns_midi = midi_communicator is None
        self.midi = midi_communicator or MidiCommunicator()
        if self.owns_midi:
            self.midi.open()
        
        # Playback state
        self.current_chord_index = 0
        self.is_playing = False
        self.is_stopped = False
        
        # Tempo tracking
        self.current_tempo_bpm: Optional[float] = None
        self.current_dynamics: float = 0.5
        self.current_articulation: float = 0.5
        
        # Timing
        self.last_chord_time: Optional[float] = None
        self.chord_start_time: Optional[float] = None
        
        # Threading
        self._lock = threading.Lock()
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self.on_chord_change: Optional[Callable[[int, Chord], None]] = None
        self.on_progression_complete: Optional[Callable[[], None]] = None
    
    def update_conductor_state(
        self,
        tempo_bpm: Optional[float],
        dynamics: float = 0.5,
        articulation: float = 0.5
    ):
        """
        Update conductor state (called continuously from main loop).
        
        Args:
            tempo_bpm: Current conductor tempo in BPM (None if not detected)
            dynamics: Dynamic level (0.0-1.0)
            articulation: Articulation (0.0=legato, 1.0=staccato)
        """
        with self._lock:
            self.current_tempo_bpm = tempo_bpm
            self.current_dynamics = dynamics
            self.current_articulation = articulation
    
    def _get_beat_duration(self) -> float:
        """
        Get current beat duration in seconds.
        
        Returns:
            Beat duration based on current tempo
        """
        tempo = self.current_tempo_bpm or self.default_bpm
        return 60.0 / tempo
    
    def _calculate_velocity(self) -> int:
        """
        Calculate MIDI velocity from current dynamics.
        
        Returns:
            MIDI velocity (0-127)
        """
        # Map dynamics to velocity range
        velocity = int(self.velocity_base + (self.current_dynamics * self.velocity_range))
        return max(0, min(127, velocity))
    
    def _playback_loop(self):
        """Background thread that handles continuous playback."""
        while not self._stop_event.is_set():
            if not self.is_playing:
                time.sleep(0.01)
                continue
            
            with self._lock:
                # Check if we've reached the end
                if self.current_chord_index >= len(self.chords):
                    if self.loop:
                        self.current_chord_index = 0
                        if self.on_progression_complete:
                            self.on_progression_complete()
                    else:
                        self.is_playing = False
                        continue
                
                # Get current chord
                chord = self.chords[self.current_chord_index]
                
                # Calculate when to play next chord
                current_time = time.time()
                
                if self.chord_start_time is None:
                    # First chord - play immediately
                    self.chord_start_time = current_time
                    velocity = self._calculate_velocity()
                    self.midi.play_chord(chord, velocity=velocity, stop_previous=True)
                    
                    if self.on_chord_change:
                        self.on_chord_change(self.current_chord_index, chord)
                    
                    self.last_chord_time = current_time
                
                else:
                    # Check if it's time for next chord
                    beat_duration = self._get_beat_duration()
                    chord_duration = chord.duration * beat_duration
                    
                    time_since_chord = current_time - self.chord_start_time
                    
                    if time_since_chord >= chord_duration:
                        # Play next chord
                        self.current_chord_index += 1
                        
                        # Check bounds again after increment
                        if self.current_chord_index >= len(self.chords):
                            if self.loop:
                                self.current_chord_index = 0
                                if self.on_progression_complete:
                                    self.on_progression_complete()
                            else:
                                self.is_playing = False
                                continue
                        
                        chord = self.chords[self.current_chord_index]
                        velocity = self._calculate_velocity()
                        self.midi.play_chord(chord, velocity=velocity, stop_previous=True)
                        
                        if self.on_chord_change:
                            self.on_chord_change(self.current_chord_index, chord)
                        
                        self.chord_start_time = current_time
                        self.last_chord_time = current_time
            
            # Small sleep to prevent busy waiting
            time.sleep(0.005)
    
    def start(self):
        """Start playback."""
        with self._lock:
            if self.is_playing:
                return
            
            self.is_playing = True
            self.is_stopped = False
            self.chord_start_time = None
            
            # Start playback thread if not already running
            if self._playback_thread is None or not self._playback_thread.is_alive():
                self._stop_event.clear()
                self._playback_thread = threading.Thread(
                    target=self._playback_loop,
                    daemon=True
                )
                self._playback_thread.start()
    
    def pause(self):
        """Pause playback."""
        with self._lock:
            self.is_playing = False
            self.midi.stop_chord()
    
    def resume(self):
        """Resume playback."""
        with self._lock:
            self.is_playing = True
            self.chord_start_time = None  # Reset timing
    
    def stop(self):
        """Stop playback and reset to beginning."""
        with self._lock:
            self.is_playing = False
            self.is_stopped = True
            self.current_chord_index = 0
            self.chord_start_time = None
            self.midi.stop_chord()
    
    def reset(self):
        """Reset to beginning without stopping."""
        with self._lock:
            self.current_chord_index = 0
            self.chord_start_time = None
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
                self.chord_start_time = None
                self.midi.stop_chord()
    
    def get_progress(self) -> tuple[int, int]:
        """
        Get current playback progress.
        
        Returns:
            Tuple of (current_index, total_chords)
        """
        with self._lock:
            return (self.current_chord_index, len(self.chords))
    
    def get_current_tempo(self) -> float:
        """Get current playback tempo."""
        with self._lock:
            return self.current_tempo_bpm or self.default_bpm
    
    def is_finished(self) -> bool:
        """Check if progression is complete."""
        with self._lock:
            return self.current_chord_index >= len(self.chords) and not self.loop
    
    def set_instruments(self, instrument_map: dict):
        """
        Set MIDI instruments for voices.
        
        Args:
            instrument_map: Dict mapping voice names to MIDI program numbers
        """
        self.midi.set_instruments(instrument_map)
    
    def cleanup(self):
        """Clean up resources."""
        # Stop playback thread
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        
        with self._lock:
            self.midi.stop_chord()
            if self.owns_midi:
                self.midi.close()
