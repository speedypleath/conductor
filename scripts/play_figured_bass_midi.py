#!/usr/bin/env python3
"""
Script to realize figured bass and play it in real-time via MIDI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator, list_midi_ports


def main():
    """Main function to parse, realize, and play via MIDI."""
    
    # Get input file path
    if len(sys.argv) > 1:
        input_filepath = sys.argv[1]
    else:
        input_filepath = Path(__file__).parent.parent / "examples" / "figured_bass.ily"
    
    # Get BPM
    bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    
    # Get velocity
    velocity = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    
    print("=" * 70)
    print("Real-time MIDI Figured Bass Player")
    print("=" * 70)
    print()
    
    # List available MIDI ports
    print("Available MIDI ports:")
    list_midi_ports()
    print()
    
    # Parse the LilyPond file
    print(f"Parsing: {input_filepath}")
    try:
        symbols = parse_lilypond_file(str(input_filepath))
    except Exception as e:
        print(f"Error parsing file: {e}")
        return 1
    
    print(f"Parsed {len(symbols)} figured bass symbols")
    print()
    
    # Create realizer and realize the figured bass
    print("Realizing figured bass...")
    realizer = FiguredBassRealizer(key="C", mode="major")
    chords = realizer.realize_figured_bass(symbols, style="strict")
    
    print(f"Realized {len(chords)} chords")
    print(f"Total duration: {sum(c.duration for c in chords)} beats")
    print()
    
    # Play via MIDI
    print("=" * 70)
    print(f"Playing at {bpm} BPM with velocity {velocity}")
    print("=" * 70)
    print()
    
    try:
        with MidiCommunicator() as midi:
            # Optional: Set instruments (General MIDI)
            # 0 = Acoustic Grand Piano
            # 32 = Acoustic Bass
            instruments = {
                'soprano': 0,  # Piano
                'alto': 0,     # Piano
                'tenor': 0,    # Piano
                'bass': 0      # Piano (or 32 for Acoustic Bass)
            }
            midi.set_instruments(instruments)
            print()
            
            # Play the chord sequence
            midi.play_chord_sequence(chords, bpm=bpm, velocity=velocity)
    
    except KeyboardInterrupt:
        print("\nPlayback stopped by user")
        return 0
    except Exception as e:
        print(f"Error during MIDI playback: {e}")
        return 1
    
    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
