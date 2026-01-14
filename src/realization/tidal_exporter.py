"""
Export realized figured bass chords to TidalCycles patterns.
"""

from typing import List
from .generator import Chord


def midi_to_tidal_note(midi_note: int) -> str:
    """
    Convert MIDI note number to TidalCycles note name.
    
    Args:
        midi_note: MIDI note number (e.g., 60 = C4)
        
    Returns:
        Tidal note name (e.g., "c4", "cs5", "bf3")
    """
    note_names = ['c', 'cs', 'd', 'ds', 'e', 'f', 'fs', 'g', 'gs', 'a', 'as', 'b']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"


def chords_to_tidal(
    chords: List[Chord],
    bpm: float = 120.0,
    sound: str = "superpiano"
) -> str:
    """
    Convert a list of realized chords to TidalCycles code.
    
    Args:
        chords: List of realized chords (SATB voicing)
        bpm: Tempo in beats per minute
        sound: TidalCycles sound/synth to use
        
    Returns:
        TidalCycles code as a string
    """
    if not chords:
        return "-- No chords to export\n"
    
    # Extract voice sequences
    soprano_notes = [midi_to_tidal_note(c.soprano) for c in chords]
    alto_notes = [midi_to_tidal_note(c.alto) for c in chords]
    tenor_notes = [midi_to_tidal_note(c.tenor) for c in chords]
    bass_notes = [midi_to_tidal_note(c.bass) for c in chords]
    
    # Extract durations (in beats)
    durations = [str(c.duration) for c in chords]
    
    # Build Tidal code
    lines = []
    lines.append("-- Generated from figured bass realization")
    lines.append(f"-- Tempo: {bpm} BPM")
    lines.append(f"-- Total chords: {len(chords)}")
    lines.append(f"-- Total duration: {sum(c.duration for c in chords)} beats")
    lines.append("")
    
    # Set tempo (1 cycle = 1 bar = 4 beats)
    lines.append(f"setcps ({bpm}/60/4)")
    lines.append("")
    
    # Helper to make patterns feel like beats
    lines.append("let beat = slow 4")
    lines.append("")
    
    # Soprano (d1)
    lines.append("-- Soprano voice")
    lines.append(f'd1 $ beat $ s "{sound}"')
    lines.append(f'  # n "{" ".join(soprano_notes)}"')
    lines.append(f'  # dur "{" ".join(durations)}"')
    lines.append("  # legato 0.95")
    lines.append("")
    
    # Alto (d2)
    lines.append("-- Alto voice")
    lines.append(f'd2 $ beat $ s "{sound}"')
    lines.append(f'  # n "{" ".join(alto_notes)}"')
    lines.append(f'  # dur "{" ".join(durations)}"')
    lines.append("  # legato 0.95")
    lines.append("")
    
    # Tenor (d3)
    lines.append("-- Tenor voice")
    lines.append(f'd3 $ beat $ s "{sound}"')
    lines.append(f'  # n "{" ".join(tenor_notes)}"')
    lines.append(f'  # dur "{" ".join(durations)}"')
    lines.append("  # legato 0.95")
    lines.append("")
    
    # Bass (d4)
    lines.append("-- Bass voice")
    lines.append(f'd4 $ beat $ s "{sound}"')
    lines.append(f'  # n "{" ".join(bass_notes)}"')
    lines.append(f'  # dur "{" ".join(durations)}"')
    lines.append("  # legato 0.95")
    lines.append("")
    
    # Add hush command at the end
    lines.append("-- To stop all voices:")
    lines.append("-- hush")
    lines.append("")
    
    return "\n".join(lines)


def export_to_tidal_file(
    chords: List[Chord],
    output_path: str,
    bpm: float = 120.0,
    sound: str = "superpiano"
) -> None:
    """
    Export chords to a TidalCycles .tidal file.
    
    Args:
        chords: List of realized chords
        output_path: Path to output .tidal file
        bpm: Tempo in beats per minute
        sound: TidalCycles sound/synth to use
    """
    tidal_code = chords_to_tidal(chords, bpm, sound)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tidal_code)
