#!/usr/bin/env python3
"""
Example script demonstrating LilyPond figured bass parsing and realization.

This script shows how to:
1. Parse a LilyPond file with figured bass notation
2. Realize the figured bass into 4-part harmony (SATB)
3. Display the results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer


def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name with octave."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"


def main():
    """Main demonstration function."""
    print("=" * 70)
    print("LilyPond Figured Bass Parser & Realizer Demo")
    print("=" * 70)
    print()

    # Get file path
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = Path(__file__).parent.parent / "examples" / "figured_bass.ily"

    print(f"Parsing file: {filepath}")
    print()

    # Parse the LilyPond file
    try:
        symbols = parse_lilypond_file(str(filepath))
    except Exception as e:
        print(f"Error parsing file: {e}")
        return 1

    print()
    print("Parsed Figured Bass Symbols:")
    print("-" * 70)
    print(f"{'#':<4} {'Bass Note':<12} {'Figures':<15} {'Accidentals':<15} {'Duration':<8}")
    print("-" * 70)

    for i, symbol in enumerate(symbols, 1):
        bass_note_name = midi_to_note_name(symbol.bass_note)
        figures_str = str(symbol.figures)
        accidentals_str = str(symbol.accidentals) if symbol.accidentals else "None"
        duration_str = f"{symbol.duration} beats"

        print(f"{i:<4} {bass_note_name:<12} {figures_str:<15} {accidentals_str:<15} {duration_str:<8}")

    print()
    print("=" * 70)
    print("Realizing Figured Bass (4-part harmony)")
    print("=" * 70)
    print()

    # Create realizer
    realizer = FiguredBassRealizer(key="C", mode="major")

    # Realize the figured bass
    chords = realizer.realize_figured_bass(symbols, style="strict")

    print("Realized Chords (SATB Voicing):")
    print("-" * 70)
    print(f"{'#':<4} {'Soprano':<12} {'Alto':<12} {'Tenor':<12} {'Bass':<12} {'Duration':<8}")
    print("-" * 70)

    for i, chord in enumerate(chords, 1):
        soprano_name = midi_to_note_name(chord.soprano)
        alto_name = midi_to_note_name(chord.alto)
        tenor_name = midi_to_note_name(chord.tenor)
        bass_name = midi_to_note_name(chord.bass)
        duration_str = f"{chord.duration} beats"

        print(f"{i:<4} {soprano_name:<12} {alto_name:<12} {tenor_name:<12} {bass_name:<12} {duration_str:<8}")

    print()
    print("=" * 70)
    print("Voice Leading Analysis")
    print("=" * 70)
    print()

    # Analyze voice leading
    for i in range(1, len(chords)):
        prev_chord = chords[i-1]
        curr_chord = chords[i]

        print(f"Chord {i} -> Chord {i+1}:")

        # Calculate motion in each voice
        voices = ['soprano', 'alto', 'tenor', 'bass']
        for voice in voices:
            prev_note = getattr(prev_chord, voice)
            curr_note = getattr(curr_chord, voice)
            motion = curr_note - prev_note

            if motion > 0:
                direction = f"up {motion} semitones"
            elif motion < 0:
                direction = f"down {abs(motion)} semitones"
            else:
                direction = "no motion"

            print(f"  {voice.capitalize():<8}: {midi_to_note_name(prev_note)} -> "
                  f"{midi_to_note_name(curr_note)} ({direction})")

        # Check for parallel fifths/octaves
        if curr_chord.has_parallel_fifths(prev_chord):
            print("  ⚠️  WARNING: Parallel fifths detected!")

        if curr_chord.has_parallel_octaves(prev_chord):
            print("  ⚠️  WARNING: Parallel octaves detected!")

        print()

    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print(f"Total chords: {len(chords)}")
    print(f"Total duration: {sum(c.duration for c in chords)} beats")

    # Calculate average voice ranges
    soprano_range = (min(c.soprano for c in chords), max(c.soprano for c in chords))
    alto_range = (min(c.alto for c in chords), max(c.alto for c in chords))
    tenor_range = (min(c.tenor for c in chords), max(c.tenor for c in chords))
    bass_range = (min(c.bass for c in chords), max(c.bass for c in chords))

    print()
    print("Voice Ranges:")
    print(f"  Soprano: {midi_to_note_name(soprano_range[0])} - {midi_to_note_name(soprano_range[1])}")
    print(f"  Alto:    {midi_to_note_name(alto_range[0])} - {midi_to_note_name(alto_range[1])}")
    print(f"  Tenor:   {midi_to_note_name(tenor_range[0])} - {midi_to_note_name(tenor_range[1])}")
    print(f"  Bass:    {midi_to_note_name(bass_range[0])} - {midi_to_note_name(bass_range[1])}")

    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
