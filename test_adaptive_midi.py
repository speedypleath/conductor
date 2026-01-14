#!/usr/bin/env python3
"""
Test script for tempo-adaptive MIDI player.
Simulates varying conductor tempo to test adaptation.
"""

import time
from pathlib import Path

from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator
from src.realization.adaptive_midi_player import AdaptiveMidiPlayer


def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"


def main():
    """Test the tempo-adaptive MIDI player."""
    print("=" * 70)
    print("Tempo-Adaptive MIDI Player Test")
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
    
    # Create adaptive player
    player = AdaptiveMidiPlayer(
        chords=chords,
        midi_communicator=midi,
        velocity_base=70,
        velocity_range=50,
        default_bpm=120.0,
        loop=False
    )
    
    # Setup callback
    def on_chord_change(index, chord):
        current_tempo = player.get_current_tempo()
        print(f"  [{current_tempo:6.1f} BPM] Chord {index + 1}/{len(chords)}: "
              f"S={midi_to_note_name(chord.soprano)} "
              f"A={midi_to_note_name(chord.alto)} "
              f"T={midi_to_note_name(chord.tenor)} "
              f"B={midi_to_note_name(chord.bass)}")
    
    player.on_chord_change = on_chord_change
    
    print()
    print("=" * 70)
    print("Testing Tempo Adaptation")
    print("=" * 70)
    print()
    print("Simulating conductor with varying tempo:")
    print("  - Start at 120 BPM")
    print("  - Slow down to 80 BPM")
    print("  - Speed up to 160 BPM")
    print("  - Return to 120 BPM")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Start playback
        player.start()
        
        # Simulate tempo changes
        tempo_sequence = [
            (120.0, 2.0),  # 120 BPM for 2 seconds
            (100.0, 2.0),  # Slow to 100 BPM
            (80.0, 2.0),   # Slow to 80 BPM
            (100.0, 2.0),  # Speed up to 100 BPM
            (140.0, 2.0),  # Speed up to 140 BPM
            (160.0, 2.0),  # Speed up to 160 BPM
            (120.0, 3.0),  # Return to 120 BPM
        ]
        
        for tempo, duration in tempo_sequence:
            print(f"Setting conductor tempo to {tempo:.0f} BPM...")
            
            # Update player tempo continuously
            end_time = time.time() + duration
            while time.time() < end_time:
                player.update_conductor_state(
                    tempo_bpm=tempo,
                    dynamics=0.6,
                    articulation=0.5
                )
                time.sleep(0.05)  # Update 20 times per second
        
        # Wait for completion
        print("\nWaiting for progression to complete...")
        while not player.is_finished():
            time.sleep(0.1)
        
        print("\nPlayback complete!")
        
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
        print(f"Chords played:    {current_chord}/{total_chords}")
        print(f"Final tempo:      {player.get_current_tempo():.1f} BPM")
        print("=" * 70)
        print()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
