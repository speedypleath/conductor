#!/usr/bin/env python3
"""
Test script for conductor MIDI integration (no camera required).
Simulates conducting beats to test the integration.
"""

import time
from pathlib import Path
from dataclasses import dataclass

from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator
from src.realization.conductor_midi_player import LoopingConductorMidiPlayer


@dataclass
class MockBeatEvent:
    """Mock beat event for testing."""
    timestamp: float
    velocity: float
    position: tuple = (0.5, 0.5, 0.0)
    acceleration: float = 5.0
    direction: str = "DOWN"
    tempo_bpm: float = 120.0
    articulation: float = 0.5


def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"


def main():
    """Test the conductor MIDI integration."""
    print("=" * 70)
    print("Conductor MIDI Integration Test")
    print("=" * 70)
    print()
    
    # Load figured bass
    figured_bass_file = Path(__file__).parent / "examples" / "figured_bass.ily"
    print(f"Loading: {figured_bass_file}")
    
    try:
        symbols = parse_lilypond_file(str(figured_bass_file))
        print(f"Parsed {len(symbols)} figured bass symbols")
        
        realizer = FiguredBassRealizer(key="C", mode="major")
        chords = realizer.realize_figured_bass(symbols, style="strict")
        print(f"Realized {len(chords)} chords")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    print()
    print("Initializing MIDI...")
    
    # Initialize MIDI
    midi = MidiCommunicator()
    midi.open()
    midi.set_instruments({
        'soprano': 0,
        'alto': 0,
        'tenor': 0,
        'bass': 0
    })
    
    # Create player
    player = LoopingConductorMidiPlayer(
        chords=chords,
        midi_communicator=midi,
        velocity_base=70,
        velocity_range=50,
        auto_start=True
    )
    
    # Setup callback
    def on_chord_change(index, chord):
        print(f"  Chord {index + 1}/{len(chords)}: "
              f"S={midi_to_note_name(chord.soprano)} "
              f"A={midi_to_note_name(chord.alto)} "
              f"T={midi_to_note_name(chord.tenor)} "
              f"B={midi_to_note_name(chord.bass)}")
    
    player.on_chord_change = on_chord_change
    
    print()
    print("=" * 70)
    print("Simulating Conducting Beats")
    print("=" * 70)
    print()
    print("Playing chords at 120 BPM (simulated conducting)")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        beat_interval = 60.0 / 120.0  # 120 BPM
        start_time = time.time()
        beat_count = 0
        
        while beat_count < len(chords) * 2:  # Play through twice
            current_time = time.time() - start_time
            
            # Create mock beat event
            beat = MockBeatEvent(
                timestamp=current_time,
                velocity=2.5 + (beat_count % 3) * 0.5,  # Vary velocity
            )
            
            # Trigger beat
            dynamics = 0.5 + (beat_count % 4) * 0.1  # Vary dynamics
            player.on_beat(beat, dynamics=dynamics, articulation=0.5)
            
            beat_count += 1
            
            # Wait for next beat
            time.sleep(beat_interval)
        
        print()
        print("Playback complete!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        print("\nCleaning up...")
        player.cleanup()
        
        current_chord, total_chords = player.get_progress()
        print()
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"Beats simulated:  {beat_count}")
        print(f"Chords played:    {current_chord}/{total_chords}")
        print(f"Loops completed:  {current_chord // total_chords}")
        print("=" * 70)
        print()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
