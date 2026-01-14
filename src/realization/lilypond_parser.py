"""
LilyPond parser for figured bass notation.
Parses LilyPond (.ly, .ily) files containing bass voice and figured bass symbols.
"""

import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from .generator import FiguredBassSymbol


@dataclass
class ParsedNote:
    """Represents a parsed note from LilyPond notation."""
    pitch_name: str  # e.g., "c", "dis", "ees"
    octave: int  # Relative octave
    duration: str  # e.g., "4", "8", "2"
    midi_note: int  # Calculated MIDI note number


@dataclass
class ParsedFigure:
    """Represents a parsed figured bass symbol."""
    figures: List[str]  # e.g., ["6"], ["7", "+"], ["6", "5", "/"]
    duration: str
    accidentals: Dict[str, str]  # figure -> accidental


class LilyPondParser:
    """Parser for LilyPond figured bass notation."""

    # Note name to chromatic offset
    NOTE_TO_CHROMATIC = {
        'c': 0, 'cis': 1, 'ces': -1,
        'd': 2, 'dis': 3, 'des': 1,
        'e': 4, 'eis': 5, 'ees': 3,
        'f': 5, 'fis': 6, 'fes': 4,
        'g': 7, 'gis': 8, 'ges': 6,
        'a': 9, 'ais': 10, 'aes': 8,
        'b': 11, 'bis': 12, 'bes': 10
    }

    # Duration to beat conversion
    DURATION_TO_BEATS = {
        '1': 4.0,
        '2': 2.0,
        '4': 1.0,
        '8': 0.5,
        '16': 0.25,
        '32': 0.125
    }

    def __init__(self, default_octave: int = 3):
        """
        Initialize parser.

        Args:
            default_octave: Default octave for bass notes (3 = C3 = MIDI 48)
        """
        self.default_octave = default_octave

    def parse_file(self, filepath: str) -> Tuple[List[FiguredBassSymbol], Dict[str, any]]: # type: ignore
        """
        Parse a LilyPond file containing figured bass notation.

        Args:
            filepath: Path to .ly or .ily file

        Returns:
            Tuple of (figured_bass_symbols, metadata)
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_string(content)

    def parse_string(self, content: str) -> Tuple[List[FiguredBassSymbol], Dict[str, any]]: # type: ignore
        """
        Parse LilyPond content string.

        Args:
            content: LilyPond notation string

        Returns:
            Tuple of (figured_bass_symbols, metadata)
        """
        # Extract bass voice
        bass_notes = self._extract_bass_voice(content)

        # Extract figured bass symbols
        figures = self._extract_figured_bass(content)

        # Combine bass notes with figures
        symbols = self._combine_bass_and_figures(bass_notes, figures)

        metadata = {
            'num_notes': len(bass_notes),
            'num_figures': len(figures),
            'num_symbols': len(symbols)
        }

        return symbols, metadata

    def _extract_bass_voice(self, content: str) -> List[ParsedNote]:
        """
        Extract bass voice notes from LilyPond content.

        Args:
            content: LilyPond string

        Returns:
            List of parsed notes
        """
        # Find \new Voice block
        voice_pattern = r'\\new\s+Voice\s*\{([^}]+)\}'
        voice_match = re.search(voice_pattern, content)

        if not voice_match:
            raise ValueError("No \\new Voice block found")

        voice_content = voice_match.group(1)

        # Remove clef directive
        voice_content = re.sub(r'\\clef\s+\w+', '', voice_content)

        # Extract notes (note name + optional duration)
        note_pattern = r'([a-g](?:is|es)?[,\']*)(\d+)?'
        notes = []

        for match in re.finditer(note_pattern, voice_content):
            pitch_str = match.group(1)
            duration = match.group(2) or '4'  # Default to quarter note

            # Parse pitch name and octave
            base_pitch = pitch_str.rstrip(",'")
            octave_marks = pitch_str[len(base_pitch):]

            # Calculate octave (apostrophe ' = +1, comma , = -1)
            octave = self.default_octave
            for char in octave_marks:
                if char == "'":
                    octave += 1
                elif char == ",":
                    octave -= 1

            # Calculate MIDI note number
            midi_note = self._calculate_midi_note(base_pitch, octave)

            notes.append(ParsedNote(
                pitch_name=base_pitch,
                octave=octave,
                duration=duration,
                midi_note=midi_note
            ))

        return notes

    def _extract_figured_bass(self, content: str) -> List[ParsedFigure]:
        """
        Extract figured bass symbols from LilyPond content.

        Args:
            content: LilyPond string

        Returns:
            List of parsed figures
        """
        # Find \figuremode block
        figure_pattern = r'\\figuremode\s*\{([^}]+)\}'
        figure_match = re.search(figure_pattern, content)

        if not figure_match:
            # No figured bass, return empty list
            return []

        figure_content = figure_match.group(1)

        # Remove bar lines
        figure_content = re.sub(r'\|', '', figure_content)

        # Extract figured bass symbols: <...>duration
        symbol_pattern = r'<([^>]*)>(\d+)?'
        figures = []

        for match in re.finditer(symbol_pattern, figure_content):
            figure_str = match.group(1).strip()
            duration = match.group(2) or '4'

            # Parse the figure content
            parsed_figures, accidentals = self._parse_figure_content(figure_str)

            figures.append(ParsedFigure(
                figures=parsed_figures,
                duration=duration,
                accidentals=accidentals
            ))

        return figures

    def _parse_figure_content(self, figure_str: str) -> Tuple[List[str], Dict[str, str]]:
        """
        Parse individual figure content (inside < >).

        Args:
            figure_str: Content inside angle brackets

        Returns:
            Tuple of (figure_list, accidentals_dict)
        """
        figures = []
        accidentals = {}

        if not figure_str or figure_str == '_':
            # Empty or underscore means no figures (root position)
            return [], {}

        # Remove optional brackets [...]
        figure_str = re.sub(r'\[|\]', '', figure_str)

        # Split by whitespace
        parts = figure_str.split()

        for part in parts:
            # Parse each part (can be: 6, 7, 5/, 6+, etc.)
            # Extract number and modifiers
            match = re.match(r'(\d+)([+\-\\/!]*)([+\-\\/!]*)', part)

            if match:
                number = match.group(1)
                modifiers = match.group(2) + match.group(3)

                figures.append(number)

                # Parse accidentals
                accidental = None
                if '+' in modifiers or '#' in modifiers:
                    accidental = '+'
                elif '-' in modifiers or 'b' in modifiers:
                    accidental = '-'
                elif '!' in modifiers:
                    accidental = '♮'  # Natural

                if accidental:
                    accidentals[number] = accidental

        return figures, accidentals

    def _combine_bass_and_figures(
        self,
        notes: List[ParsedNote],
        figures: List[ParsedFigure]
    ) -> List[FiguredBassSymbol]:
        """
        Combine bass notes with figured bass symbols.

        Args:
            notes: List of bass notes
            figures: List of figured bass symbols

        Returns:
            List of FiguredBassSymbol objects
        """
        symbols = []

        # If no figures, use root position for all notes
        if not figures:
            figures = [ParsedFigure([], note.duration, {}) for note in notes]

        # Ensure we have equal numbers (pad or truncate as needed)
        max_len = max(len(notes), len(figures))

        for i in range(max_len):
            if i >= len(notes):
                # No more notes, skip
                break

            note = notes[i]
            figure = figures[i] if i < len(figures) else ParsedFigure([], note.duration, {})

            # Convert duration to beats
            duration_beats = self.DURATION_TO_BEATS.get(note.duration, 1.0)

            # Convert figure notation to standard figured bass
            figure_str = self._figure_to_standard_notation(figure.figures, figure.accidentals)

            # Create FiguredBassSymbol
            symbol = FiguredBassSymbol.from_string(
                bass_note=note.midi_note,
                figure_str=figure_str,
                duration=duration_beats
            )

            symbols.append(symbol)

        return symbols

    def _figure_to_standard_notation(
        self,
        figures: List[str],
        accidentals: Dict[str, str]
    ) -> str:
        """
        Convert parsed figures to standard notation string.

        Args:
            figures: List of figure numbers
            accidentals: Dictionary of accidentals

        Returns:
            Standard notation string (e.g., "6", "6/4", "7")
        """
        if not figures:
            return ""  # Root position

        # Sort figures in ascending order
        sorted_figures = sorted(figures, key=int)

        # Build notation string
        notation_parts = []
        for fig in sorted_figures:
            part = fig

            # Add accidental if present
            if fig in accidentals:
                acc = accidentals[fig]
                if acc == '+':
                    part += '#'
                elif acc == '-':
                    part += 'b'

            notation_parts.append(part)

        return '/'.join(notation_parts)

    def _calculate_midi_note(self, pitch_name: str, octave: int) -> int:
        """
        Calculate MIDI note number from pitch name and octave.

        Args:
            pitch_name: Note name (e.g., "c", "dis", "ees")
            octave: Octave number (C4 = octave 4)

        Returns:
            MIDI note number
        """
        chromatic_offset = self.NOTE_TO_CHROMATIC.get(pitch_name, 0)
        # MIDI note 60 = C4
        # Each octave is 12 semitones
        midi_note = (octave + 1) * 12 + chromatic_offset

        return midi_note


def parse_lilypond_file(filepath: str) -> List[FiguredBassSymbol]:
    """
    Convenience function to parse a LilyPond file.

    Args:
        filepath: Path to .ly or .ily file

    Returns:
        List of FiguredBassSymbol objects
    """
    parser = LilyPondParser()
    symbols, metadata = parser.parse_file(filepath)

    print(f"Parsed {metadata['num_notes']} notes and {metadata['num_figures']} figures")
    print(f"Generated {metadata['num_symbols']} figured bass symbols")

    return symbols


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "../../examples/figured_bass.ily"

    try:
        symbols = parse_lilypond_file(filepath)

        print("\nParsed symbols:")
        for i, symbol in enumerate(symbols):
            print(f"{i+1}. Bass note: {symbol.bass_note} (MIDI), "
                  f"Figures: {symbol.figures}, "
                  f"Accidentals: {symbol.accidentals}, "
                  f"Duration: {symbol.duration} beats")

    except Exception as e:
        print(f"Error parsing file: {e}")
        import traceback
        traceback.print_exc()
