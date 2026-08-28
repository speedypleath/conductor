# Figured Bass Realization & MIDI Engine

This module provides tools for parsing figured bass notation from LilyPond files, harmonizing them into complete 4-part (SATB - Soprano, Alto, Tenor, Bass) voicings following common practice voice-leading rules, and playing or exporting them via multi-channel MIDI and TidalCycles.

---

## Features

- **LilyPond Parser**: Parses `.ly` and `.ily` files with figured bass expressions (`\figuremode`), extracting notes, accidentals, and durations.
- **Rule-Based Realizer**: Generates 4-part SATB voicings adhering to classical voice-leading rules (voice ranges, spacing, common-tone retention, and elimination of parallel fifths/octaves).
- **Real-Time MIDI Communicator**: Multi-channel MIDI output engine mapping SATB voices to dedicated MIDI channels (1–4) with custom instrument patches and velocity control.
- **Adaptive & Conductor MIDI Players**: Sequencers that synchronize chord playback with external conductor timing, tempo changes, and dynamics.
- **TidalCycles Exporter**: Exports realized harmonic progressions into TidalCycles live coding patterns.

---

## Architecture & Module Layout

```
src/realization/
├── lilypond_parser.py       # LilyPond figured bass tokenizer & AST parser
├── generator.py             # 4-part SATB harmony realizer & voice leading rules
├── midi_communicator.py     # Multi-channel MIDI output handler (Mido/RT-MIDI)
├── adaptive_midi_player.py  # Dynamic tempo-adaptive playback engine
├── conductor_midi_player.py # Interactive beat-synchronized chord player
└── tidal_exporter.py        # TidalCycles pattern exporter
```

---

## Quick Usage Examples

### 1. Python API: Parse, Realize, and Play

```python
from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator

# 1. Parse LilyPond figured bass
symbols = parse_lilypond_file("examples/figured_bass.ily")

# 2. Realize into 4-part SATB harmony
realizer = FiguredBassRealizer(key="C", mode="major")
chords = realizer.realize_figured_bass(symbols, style="strict")

# 3. Play realized chords over MIDI
with MidiCommunicator() as midi:
    midi.set_instruments({
        'soprano': 0,   # Acoustic Grand Piano
        'alto': 0,
        'tenor': 0,
        'bass': 32      # Acoustic Bass
    })
    midi.play_chord_sequence(chords, bpm=120, velocity=80)
```

### 2. Command-Line Scripts

```bash
# Realize figured bass and print chord voicings with voice-leading analysis
python scripts/realize_figured_bass.py examples/figured_bass.ily

# Play figured bass over MIDI (file, BPM, velocity)
python scripts/play_figured_bass_midi.py examples/figured_bass.ily 120 85

# Export realized progression to TidalCycles pattern
python scripts/export_to_tidal.py examples/figured_bass.ily output.tidal
```

---

## LilyPond File Format

The parser expects LilyPond files containing both a bass voice and a `\figuremode` block:

```lilypond
<<
  \new Voice { 
    \clef bass 
    c4 f g c | d g c2
  }
  \new FiguredBass {
    \figuremode {
      <_>4 <6> <7> <_> | <6> <7> <_>2
    }
  }
>>
```

### Supported Notation
- **Bass Notes**: Full chromatic scale (`c`, `cis`, `des`, `d`, `ees`, `e`, `f`, `fis`, `g`, `gis`, `aes`, `a`, `bes`, `b`).
- **Octave Notation**: Relative to octave 3 using apostrophes (`'`) for higher octaves or commas (`,`) for lower octaves.
- **Figures**:
  - Root position: `<5 3>`, `<5>`, or `<_>` (empty)
  - First inversion (6th chord): `<6>` or `<6 3>`
  - Second inversion (6/4 chord): `<6 4>`
  - 7th chords & inversions: `<7>`, `<6 5>`, `<4 3>`, `<4 2>`
- **Accidentals on figures**: `+` (sharp), `-` (flat), `!` (natural).
- **Durations**: Whole (`1`), half (`2`), quarter (`4`), 8th (`8`), 16th (`16`), 32nd (`32`).

---

## Voice Leading Rules

The realizer enforces common-practice harmonic voice leading:

1. **Voice Ranges**:
   - **Soprano**: C4 (60) to A5 (81)
   - **Alto**: G3 (55) to D5 (74)
   - **Tenor**: C3 (48) to A4 (69)
   - **Bass**: E2 (40) to E4 (64)

2. **Spacing**:
   - Upper voice intervals (Soprano–Alto, Alto–Tenor) must not exceed an octave.
   - Bass–Tenor interval can exceed an octave.

3. **Motion & Doubling**:
   - Strictly prohibits parallel fifths and octaves in `style="strict"`.
   - Prioritizes minimal voice movement and retention of common tones.
   - Favors contrary motion between Soprano and Bass.
   - Prioritizes doubling the root or fifth in triads.

---

## MIDI Configuration & Channel Routing

### Channel Mapping
The `MidiCommunicator` routes voices to separate MIDI channels:
- **Channel 0 (MIDI Ch 1)**: Soprano
- **Channel 1 (MIDI Ch 2)**: Alto
- **Channel 2 (MIDI Ch 3)**: Tenor
- **Channel 3 (MIDI Ch 4)**: Bass

### Routing to DAWs (Ableton, Logic, Reaper)
1. **macOS**: Enable **IAC Driver** in *Audio MIDI Setup* > *MIDI Studio*.
2. **Windows**: Use [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html).
3. **DAW Setup**: Create 4 tracks listening to MIDI Channels 1–4 of the virtual port.

---

## Testing

Run unit tests covering parser and voice-leading generation:

```bash
pytest tests/test_lilypond_parser.py -v
```
