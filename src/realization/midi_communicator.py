"""
Real-time MIDI communicator for playing realized figured bass chords.
Sends MIDI messages to output devices for live performance.
"""

import time
from typing import List, Optional
from .generator import Chord

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    print("Warning: mido library not installed. Install with: pip install mido python-rtmidi")


class MidiCommunicator:
    """Real-time MIDI output for chord sequences."""
    
    def __init__(
        self,
        port_name: Optional[str] = None,
        channel_mapping: Optional[dict] = None
    ):
        """
        Initialize MIDI communicator.
        
        Args:
            port_name: MIDI output port name (None = use default/virtual)
            channel_mapping: Dict mapping voice names to MIDI channels
                           e.g., {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3}
        """
        if not MIDO_AVAILABLE:
            raise ImportError("mido library required. Install with: pip install mido python-rtmidi")
        
        self.port_name = port_name
        self.channel_mapping = channel_mapping or {
            'soprano': 0,
            'alto': 1,
            'tenor': 2,
            'bass': 3
        }
        
        self.port = None
        self.active_notes = {voice: None for voice in self.channel_mapping.keys()}
        
    def __enter__(self):
        """Context manager entry - open MIDI port."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close MIDI port."""
        self.close()
    
    def open(self):
        """Open MIDI output port."""
        if self.port is not None:
            return
        
        try:
            if self.port_name:
                # Use specified port
                self.port = mido.open_output(self.port_name)
                print(f"Opened MIDI port: {self.port_name}")
            else:
                # Try to open default port or create virtual port
                available_ports = mido.get_output_names()
                if available_ports:
                    self.port = mido.open_output(available_ports[0])
                    print(f"Opened MIDI port: {available_ports[0]}")
                else:
                    # Create virtual port
                    self.port = mido.open_output('Figured Bass Realizer', virtual=True)
                    print("Created virtual MIDI port: Figured Bass Realizer")
        except Exception as e:
            print(f"Error opening MIDI port: {e}")
            print("Available ports:", mido.get_output_names())
            raise
    
    def close(self):
        """Close MIDI port and stop all notes."""
        if self.port is None:
            return
        
        # Send note off for any active notes
        for voice, note in self.active_notes.items():
            if note is not None:
                channel = self.channel_mapping[voice]
                self.port.send(mido.Message('note_off', note=note, channel=channel))
        
        self.port.close()
        self.port = None
        print("MIDI port closed")
    
    def send_note_on(self, note: int, velocity: int, channel: int):
        """
        Send MIDI note on message.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (0-127)
            channel: MIDI channel (0-15)
        """
        if self.port is None:
            raise RuntimeError("MIDI port not open. Call open() first.")
        
        msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
        self.port.send(msg)
    
    def send_note_off(self, note: int, channel: int):
        """
        Send MIDI note off message.
        
        Args:
            note: MIDI note number (0-127)
            channel: MIDI channel (0-15)
        """
        if self.port is None:
            raise RuntimeError("MIDI port not open. Call open() first.")
        
        msg = mido.Message('note_off', note=note, channel=channel)
        self.port.send(msg)
    
    def play_chord(
        self,
        chord: Chord,
        velocity: int = 80,
        stop_previous: bool = True
    ):
        """
        Play a single chord by sending MIDI note on messages.
        
        Args:
            chord: Chord to play
            velocity: MIDI velocity (0-127)
            stop_previous: If True, stop previously playing notes
        """
        if self.port is None:
            raise RuntimeError("MIDI port not open. Call open() first.")
        
        # Stop previous notes if requested
        if stop_previous:
            for voice, note in self.active_notes.items():
                if note is not None:
                    channel = self.channel_mapping[voice]
                    self.send_note_off(note, channel)
        
        # Play new chord
        voices = {
            'soprano': chord.soprano,
            'alto': chord.alto,
            'tenor': chord.tenor,
            'bass': chord.bass
        }
        
        for voice, note in voices.items():
            channel = self.channel_mapping[voice]
            self.send_note_on(note, velocity, channel)
            self.active_notes[voice] = note
    
    def stop_chord(self):
        """Stop all currently playing notes."""
        if self.port is None:
            return
        
        for voice, note in self.active_notes.items():
            if note is not None:
                channel = self.channel_mapping[voice]
                self.send_note_off(note, channel)
                self.active_notes[voice] = None
    
    def play_chord_sequence(
        self,
        chords: List[Chord],
        bpm: float = 120.0,
        velocity: int = 80
    ):
        """
        Play a sequence of chords in real-time.
        
        Args:
            chords: List of chords to play
            bpm: Tempo in beats per minute
            velocity: MIDI velocity (0-127)
        """
        if not chords:
            print("No chords to play")
            return
        
        if self.port is None:
            raise RuntimeError("MIDI port not open. Call open() first.")
        
        # Calculate beat duration in seconds
        beat_duration = 60.0 / bpm
        
        print(f"Playing {len(chords)} chords at {bpm} BPM")
        print("Press Ctrl+C to stop")
        
        try:
            for i, chord in enumerate(chords):
                print(f"Chord {i+1}/{len(chords)}: "
                      f"S={chord.soprano} A={chord.alto} T={chord.tenor} B={chord.bass} "
                      f"(duration={chord.duration} beats)")
                
                # Play the chord
                self.play_chord(chord, velocity=velocity)
                
                # Wait for the chord duration
                time.sleep(chord.duration * beat_duration)
            
            # Stop final chord
            self.stop_chord()
            print("Playback complete")
            
        except KeyboardInterrupt:
            print("\nPlayback interrupted")
            self.stop_chord()
    
    def send_program_change(self, program: int, channel: int):
        """
        Send MIDI program change message.
        
        Args:
            program: MIDI program number (0-127)
            channel: MIDI channel (0-15)
        """
        if self.port is None:
            raise RuntimeError("MIDI port not open. Call open() first.")
        
        msg = mido.Message('program_change', program=program, channel=channel)
        self.port.send(msg)
    
    def set_instruments(self, instrument_map: dict):
        """
        Set MIDI instruments for each voice.
        
        Args:
            instrument_map: Dict mapping voice names to MIDI program numbers
                          e.g., {'soprano': 0, 'alto': 0, 'tenor': 0, 'bass': 32}
        """
        for voice, program in instrument_map.items():
            if voice in self.channel_mapping:
                channel = self.channel_mapping[voice]
                self.send_program_change(program, channel)
                print(f"Set {voice} (channel {channel}) to program {program}")


def list_midi_ports():
    """List available MIDI output ports."""
    if not MIDO_AVAILABLE:
        print("mido library not installed. Install with: pip install mido python-rtmidi")
        return []
    
    ports = mido.get_output_names()
    print("Available MIDI output ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port}")
    
    if not ports:
        print("  (No MIDI ports found - will create virtual port)")
    
    return ports
