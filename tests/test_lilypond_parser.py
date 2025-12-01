"""Tests for LilyPond parser."""

import pytest
from pathlib import Path
from src.realization.lilypond_parser import LilyPondParser, parse_lilypond_file
from src.realization.generator import FiguredBassSymbol, FiguredBassRealizer


class TestLilyPondParser:
    """Test suite for LilyPond parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LilyPondParser()

    def test_parse_simple_note(self):
        """Test parsing a simple bass note."""
        content = """
        <<
          \\new Voice { \\clef bass c4 }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 1
        assert symbols[0].bass_note == 48  # C3 in MIDI
        assert symbols[0].duration == 1.0  # Quarter note

    def test_parse_bass_voice_with_accidentals(self):
        """Test parsing bass notes with sharps and flats."""
        content = """
        <<
          \\new Voice { \\clef bass cis4 des eis fes }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <5 3> <5 3> <5 3>
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 4
        assert symbols[0].bass_note == 49  # C#3
        assert symbols[1].bass_note == 49  # Db3 (enharmonic to C#)
        assert symbols[2].bass_note == 53  # E#3 (F)
        assert symbols[3].bass_note == 52  # Fb3 (E)

    def test_parse_bass_voice_with_octaves(self):
        """Test parsing bass notes with different octaves."""
        content = """
        <<
          \\new Voice { \\clef bass c,4 c c' c'' }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <5 3> <5 3> <5 3>
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 4
        assert symbols[0].bass_note == 36  # C2
        assert symbols[1].bass_note == 48  # C3
        assert symbols[2].bass_note == 60  # C4
        assert symbols[3].bass_note == 72  # C5

    def test_parse_figured_bass_symbols(self):
        """Test parsing various figured bass symbols."""
        content = """
        <<
          \\new Voice { \\clef bass c4 d e f g }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <6>4 <6 4>4 <7>4 <6 5>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 5

        # Root position (5/3)
        assert set(symbols[0].figures) == {3, 5}

        # First inversion (6)
        assert set(symbols[1].figures) == {3, 6}

        # Second inversion (6/4)
        assert set(symbols[2].figures) == {4, 6}

        # Seventh chord (7)
        assert set(symbols[3].figures) == {3, 5, 7}

        # First inversion seventh (6/5)
        # Note: The generator handles this internally as {3, 5, 6}
        assert set(symbols[4].figures) == {5, 6}

    def test_parse_figured_bass_with_accidentals(self):
        """Test parsing figured bass with accidentals."""
        content = """
        <<
          \\new Voice { \\clef bass c4 d e }
          \\new FiguredBass {
            \\figuremode {
              <6+>4 <7\\+>4 <6 5/>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 3

        # Check that accidentals are parsed (raised 6)
        assert 6 in symbols[0].accidentals

        # Check raised 7
        assert 7 in symbols[1].accidentals

    def test_parse_different_durations(self):
        """Test parsing notes with different durations."""
        content = """
        <<
          \\new Voice { \\clef bass c1 d2 e4 f8 g16 }
          \\new FiguredBass {
            \\figuremode {
              <5 3>1 <5 3>2 <5 3>4 <5 3>8 <5 3>16
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 5
        assert symbols[0].duration == 4.0  # Whole note
        assert symbols[1].duration == 2.0  # Half note
        assert symbols[2].duration == 1.0  # Quarter note
        assert symbols[3].duration == 0.5  # Eighth note
        assert symbols[4].duration == 0.25  # Sixteenth note

    def test_parse_empty_figured_bass(self):
        """Test parsing with underscore (empty figure)."""
        content = """
        <<
          \\new Voice { \\clef bass c4 d }
          \\new FiguredBass {
            \\figuremode {
              <_>4 <5 3>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert len(symbols) == 2
        # Empty figure should result in root position
        assert symbols[0].figures == [3, 5]

    def test_parse_example_file(self):
        """Test parsing the example figured_bass.ily file."""
        example_path = Path(__file__).parent.parent / "examples" / "figured_bass.ily"

        if not example_path.exists():
            pytest.skip("Example file not found")

        symbols = parse_lilypond_file(str(example_path))

        assert len(symbols) > 0
        assert all(isinstance(s, FiguredBassSymbol) for s in symbols)
        assert all(40 <= s.bass_note <= 70 for s in symbols)  # Reasonable bass range

    def test_integration_with_realizer(self):
        """Test that parsed symbols work with FiguredBassRealizer."""
        content = """
        <<
          \\new Voice { \\clef bass c4 f g c }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <5 3>4 <7>4 <5 3>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        # Create realizer
        realizer = FiguredBassRealizer(key="C", mode="major")

        # Realize the progression
        chords = realizer.realize_figured_bass(symbols, style="strict")

        assert len(chords) == 4
        assert all(hasattr(c, 'bass') for c in chords)
        assert all(hasattr(c, 'soprano') for c in chords)

        # Check that bass notes match
        for i, chord in enumerate(chords):
            assert chord.bass == symbols[i].bass_note

    def test_metadata(self):
        """Test that metadata is correctly returned."""
        content = """
        <<
          \\new Voice { \\clef bass c4 d e }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <6>4 <6 4>4
            }
          }
        >>
        """
        symbols, metadata = self.parser.parse_string(content)

        assert metadata['num_notes'] == 3
        assert metadata['num_figures'] == 3
        assert metadata['num_symbols'] == 3

    def test_error_handling_no_voice(self):
        """Test error handling when Voice block is missing."""
        content = """
        <<
          \\new FiguredBass {
            \\figuremode {
              <5 3>4
            }
          }
        >>
        """

        with pytest.raises(ValueError, match="No.*Voice block found"):
            self.parser.parse_string(content)

    def test_note_name_conversion(self):
        """Test all note names convert correctly."""
        test_cases = [
            ('c', 3, 48),   # C3
            ('cis', 3, 49), # C#3
            ('des', 3, 49), # Db3
            ('d', 3, 50),   # D3
            ('dis', 3, 51), # D#3
            ('ees', 3, 51), # Eb3
            ('e', 3, 52),   # E3
            ('f', 3, 53),   # F3
            ('fis', 3, 54), # F#3
            ('ges', 3, 54), # Gb3
            ('g', 3, 55),   # G3
            ('gis', 3, 56), # G#3
            ('aes', 3, 56), # Ab3
            ('a', 3, 57),   # A3
            ('ais', 3, 58), # A#3
            ('bes', 3, 58), # Bb3
            ('b', 3, 59),   # B3
        ]

        for pitch_name, octave, expected_midi in test_cases:
            result = self.parser._calculate_midi_note(pitch_name, octave)
            assert result == expected_midi, f"Failed for {pitch_name}{octave}: expected {expected_midi}, got {result}"


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_progression(self):
        """Test parsing and realizing a complete progression."""
        content = """
        <<
          \\new Voice { \\clef bass c4 f g c }
          \\new FiguredBass {
            \\figuremode {
              <5 3>4 <5 3>4 <7>4 <5 3>4
            }
          }
        >>
        """

        # Parse
        parser = LilyPondParser()
        symbols, _ = parser.parse_string(content)

        # Realize
        realizer = FiguredBassRealizer(key="C", mode="major")
        chords = realizer.realize_figured_bass(symbols)

        # Verify complete 4-voice texture
        assert all(len(c.get_notes()) == 4 for c in chords)

        # Verify voice ranges are respected
        for chord in chords:
            assert 40 <= chord.bass <= 64
            assert 48 <= chord.tenor <= 69
            assert 55 <= chord.alto <= 74
            assert 60 <= chord.soprano <= 81


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
