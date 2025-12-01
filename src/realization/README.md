# Figured Bass Realization Module

This module provides tools for parsing and realizing figured bass notation from LilyPond files into complete 4-part harmony (SATB - Soprano, Alto, Tenor, Bass).

## Features

- **LilyPond Parser**: Parses `.ly` and `.ily` files containing figured bass notation
- **Figured Bass Realizer**: Generates complete 4-part harmonizations following common practice voice leading rules
- **Voice Leading Analysis**: Checks for parallel fifths, octaves, and other voice leading issues
- **Flexible Configuration**: Supports different keys, modes, and realization styles

## Installation

The module is part of the gesture-conductor project. All dependencies are managed via `uv`:

```bash
uv sync
```

## Usage

### Basic Example

```python
from src.realization import parse_lilypond_file, FiguredBassRealizer

# Parse a LilyPond file
symbols = parse_lilypond_file("examples/figured_bass.ily")

# Create a realizer
realizer = FiguredBassRealizer(key="C", mode="major")

# Realize the figured bass
chords = realizer.realize_figured_bass(symbols, style="strict")

# Access the voicings
for chord in chords:
    print(f"Soprano: {chord.soprano}, Alto: {chord.alto}, "
          f"Tenor: {chord.tenor}, Bass: {chord.bass}")
```

### Running the Demo

```bash
uv run python examples/realize_figured_bass.py [filepath]
```

If no filepath is provided, it uses the default `examples/figured_bass.ily` file.

## LilyPond File Format

The parser expects LilyPond files with the following structure:

```lilypond
<<
  \new Voice { \clef bass c4 d e f g }
  \new FiguredBass {
    \figuremode {
      <5 3>4 <6>4 <6 4>4 <7>4 <6 5>4
    }
  }
>>
```

### Supported Features

- **Bass Notes**: All chromatic pitches (c, cis, des, etc.)
- **Octave Markings**: Apostrophes (') for higher octaves, commas (,) for lower octaves
- **Figured Bass Symbols**:
  - Root position: `<5 3>` or `<_>` (empty)
  - First inversion: `<6>` or `<6 3>`
  - Second inversion: `<6 4>`
  - Seventh chords: `<7>`, `<6 5>`, `<4 3>`, `<4 2>`
- **Accidentals**: `+` (sharp), `-` (flat), `!` (natural)
- **Durations**: 1, 2, 4, 8, 16, 32 (whole, half, quarter, eighth, sixteenth, thirty-second notes)

## API Reference

### LilyPondParser

```python
parser = LilyPondParser(default_octave=3)
symbols, metadata = parser.parse_file("path/to/file.ily")
```

**Parameters:**
- `default_octave` (int): Default octave for bass notes (default: 3)

**Returns:**
- `symbols`: List of `FiguredBassSymbol` objects
- `metadata`: Dictionary with parsing statistics

### FiguredBassRealizer

```python
realizer = FiguredBassRealizer(
    key="C",
    mode="major",
    voice_ranges=None
)
chords = realizer.realize_figured_bass(symbols, style="strict")
```

**Parameters:**
- `key` (str): Key signature (e.g., "C", "G", "Bb")
- `mode` (str): Mode ("major" or "minor")
- `voice_ranges` (dict, optional): Custom voice ranges
- `style` (str): Realization style ("strict", "free", "keyboard")

**Returns:**
- List of `Chord` objects with bass, tenor, alto, soprano voicings

### FiguredBassSymbol

Represents a figured bass symbol with:
- `bass_note` (int): MIDI note number for bass
- `figures` (list): Interval numbers above bass
- `accidentals` (dict): Accidentals for specific figures
- `duration` (float): Duration in beats

### Chord

Represents a realized chord with:
- `bass` (int): MIDI note for bass
- `tenor` (int): MIDI note for tenor
- `alto` (int): MIDI note for alto
- `soprano` (int): MIDI note for soprano
- `duration` (float): Duration in beats

**Methods:**
- `get_notes()`: Returns list of all notes
- `get_intervals()`: Returns intervals between voices
- `has_parallel_fifths(other)`: Checks for parallel fifths
- `has_parallel_octaves(other)`: Checks for parallel octaves

## Voice Leading Rules

The realizer follows common practice voice leading rules:

1. **Voice Ranges** (default SATB ranges):
   - Soprano: C4 (60) to A5 (81)
   - Alto: G3 (55) to D5 (74)
   - Tenor: C3 (48) to A4 (69)
   - Bass: E2 (40) to E4 (64)

2. **Spacing**:
   - Upper voices (soprano, alto, tenor) should not exceed an octave between adjacent voices
   - Bass can be further from tenor

3. **Voice Leading**:
   - Prefers minimal motion between chords
   - Avoids parallel fifths and octaves in strict style
   - Maintains common tones when possible
   - Prefers contrary motion between bass and soprano

4. **Doubling**:
   - All chord tones should be present
   - Minimum of 3 different pitch classes

## Testing

Run the test suite:

```bash
uv run pytest tests/test_lilypond_parser.py -v
```

All tests should pass, covering:
- Note parsing with various accidentals and octaves
- Figured bass symbol parsing
- Duration parsing
- Integration with the realizer
- Error handling

## Examples

See `scripts/realize_figured_bass.py` for a complete demonstration of parsing and realizing figured bass with detailed voice leading analysis.
