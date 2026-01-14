#!/usr/bin/env python3
"""
Script to realize figured bass and export to TidalCycles format.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.tidal_exporter import export_to_tidal_file


def main():
    """Main function to parse, realize, and export to Tidal."""
    
    # Get input file path
    if len(sys.argv) > 1:
        input_filepath = sys.argv[1]
    else:
        input_filepath = Path(__file__).parent.parent / "examples" / "figured_bass.ily"
    
    # Get output file path
    if len(sys.argv) > 2:
        output_filepath = sys.argv[2]
    else:
        output_filepath = Path(__file__).parent.parent / "tidal" / "realized_bass.tidal"
    
    # Get BPM
    bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
    
    print(f"Parsing: {input_filepath}")
    
    # Parse the LilyPond file
    try:
        symbols = parse_lilypond_file(str(input_filepath))
    except Exception as e:
        print(f"Error parsing file: {e}")
        return 1
    
    print(f"Parsed {len(symbols)} figured bass symbols")
    
    # Create realizer and realize the figured bass
    realizer = FiguredBassRealizer(key="C", mode="major")
    chords = realizer.realize_figured_bass(symbols, style="strict")
    
    print(f"Realized {len(chords)} chords")
    
    # Export to Tidal
    export_to_tidal_file(chords, str(output_filepath), bpm=bpm, sound="superpiano")
    
    print(f"Exported to: {output_filepath}")
    print(f"Tempo: {bpm} BPM")
    print(f"Total duration: {sum(c.duration for c in chords)} beats")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
