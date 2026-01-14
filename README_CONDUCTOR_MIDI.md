# Gesture Conductor + MIDI Figured Bass Integration

Real-time gesture-controlled figured bass playback. Conduct with your hand to advance through a 4-part harmony realization, with each beat triggering the next chord via MIDI.

## Features

- **Beat-synchronized playback**: Each conducting beat advances to the next chord
- **Dynamic control**: Gesture velocity affects MIDI velocity (volume)
- **Articulation mapping**: Conducting style affects note articulation
- **Looping playback**: Progression loops automatically
- **Visual feedback**: See your conducting gestures and current chord position
- **Real-time MIDI output**: Send to DAW, software synth, or hardware

## Quick Start

### 1. Setup

```bash
# Install dependencies (if not already done)
./setup_midi.sh
source venv/bin/activate
```

### 2. Run the Integrated System

```bash
# Use default figured bass example (110 chords)
python main_conductor_midi.py

# Or specify your own LilyPond file
python main_conductor_midi.py examples/figured_bass_extended.ily
```

### 3. Conduct!

- **Start**: Press SPACE to begin
- **Conduct**: Move your hand up and down to create beats
- **Each beat** = next chord in the progression
- **Faster conducting** = higher tempo (but same chord progression)
- **Stronger gestures** = louder chords (higher MIDI velocity)

## Controls

| Key | Action |
|-----|--------|
| SPACE | Start/Pause playback |
| R | Reset to beginning |
| C | Clear gesture history |
| Q | Quit |

## How It Works

1. **Gesture Detection**: Camera tracks your hand position
2. **Beat Detection**: Analyzes hand motion to detect conducting beats
3. **Chord Advancement**: Each beat triggers the next chord in the realized figured bass
4. **MIDI Output**: Sends 4-voice SATB harmony to MIDI channels 1-4
5. **Dynamic Control**: Gesture velocity and articulation affect playback

## MIDI Setup

### Connect to a DAW

1. Configure your DAW to receive MIDI from "Figured Bass Realizer" virtual port
2. Create 4 MIDI tracks for SATB voices (channels 1-4)
3. Load instruments (piano, strings, etc.)
4. Run the application and start conducting

### MIDI Channel Mapping

- **Channel 1** (0): Soprano voice
- **Channel 2** (1): Alto voice
- **Channel 3** (2): Tenor voice
- **Channel 4** (3): Bass voice

## Musical Parameters

The system maps conducting gestures to musical parameters:

- **Tempo**: Detected from beat intervals (30-240 BPM)
- **Dynamics**: Gesture velocity → MIDI velocity (0-127)
- **Articulation**: Gesture sharpness → note duration/attack
- **Beat strength**: Acceleration → emphasis

## Creating Custom Figured Bass

Create a LilyPond file with figured bass notation:

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

Then run:
```bash
python main_conductor_midi.py your_file.ily
```

## Tips for Best Results

1. **Lighting**: Ensure good lighting for hand tracking
2. **Background**: Plain background works best
3. **Distance**: Position hand 1-2 feet from camera
4. **Movement**: Clear up-down motions for beat detection
5. **Tempo**: Start slow, increase speed as comfortable
6. **Dynamics**: Vary gesture strength for expressive dynamics

## Architecture

```
Camera → Hand Tracking → Beat Detection → Chord Advancement → MIDI Output
                ↓              ↓                ↓
         Position Trail   Tempo/Articulation   4-Voice SATB
```

## Troubleshooting

**No MIDI output?**
- Check that MIDI port is created: "Figured Bass Realizer"
- Verify DAW is listening on correct MIDI channels
- Check MIDI monitor in your DAW

**Beats not detected?**
- Ensure clear up-down hand motion
- Check lighting and camera quality
- Try larger, slower gestures
- Verify hand is visible in frame

**Chords not advancing?**
- Press SPACE to start playback
- Ensure conducting gestures are detected (watch beat counter)
- Check that you're not paused

## Examples

### Short Example (6 chords)
```bash
python main_conductor_midi.py examples/figured_bass.ily
```

### Extended Example (14 bars)
```bash
python main_conductor_midi.py examples/figured_bass_extended.ily
```

### Long Example (110 chords, 16 bars)
```bash
python main_conductor_midi.py examples/figured_bass_long.ily
```

## Advanced Usage

### Custom Instruments

Edit `main_conductor_midi.py` to change instruments:

```python
midi.set_instruments({
    'soprano': 0,   # Acoustic Grand Piano
    'alto': 40,     # Violin
    'tenor': 41,    # Viola
    'bass': 42      # Cello
})
```

### Velocity Range

Adjust dynamic range in the player initialization:

```python
player = LoopingConductorMidiPlayer(
    chords=chords,
    velocity_base=60,    # Minimum velocity
    velocity_range=60,   # Range (60-120)
    auto_start=False
)
```

## Integration with Other Systems

The conductor MIDI player can be integrated with:
- **Live performance systems**
- **Music education tools**
- **Interactive installations**
- **Composition workflows**

See `src/realization/conductor_midi_player.py` for the API.
