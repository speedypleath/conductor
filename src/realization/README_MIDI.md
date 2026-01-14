# Real-time MIDI Playback

The MIDI communicator enables real-time playback of realized figured bass through MIDI output.

## Installation

Install the required MIDI dependencies:

```bash
pip install mido python-rtmidi
```

Or install all project dependencies:

```bash
pip install -e .
```

## Usage

### Basic Playback

Play a figured bass file with default settings (120 BPM):

```bash
python3 scripts/play_figured_bass_midi.py examples/figured_bass.ily
```

### Custom Tempo and Velocity

```bash
python3 scripts/play_figured_bass_midi.py examples/figured_bass.ily 90 100
# Arguments: <input_file> <bpm> <velocity>
```

### Programmatic Usage

```python
from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator

# Parse and realize
symbols = parse_lilypond_file("examples/figured_bass.ily")
realizer = FiguredBassRealizer(key="C", mode="major")
chords = realizer.realize_figured_bass(symbols)

# Play in real-time
with MidiCommunicator() as midi:
    # Optional: set instruments (General MIDI program numbers)
    midi.set_instruments({
        'soprano': 0,  # Acoustic Grand Piano
        'alto': 0,
        'tenor': 0,
        'bass': 32     # Acoustic Bass
    })
    
    # Play the sequence
    midi.play_chord_sequence(chords, bpm=120, velocity=80)
```

## MIDI Channel Mapping

By default, the four SATB voices are mapped to MIDI channels:
- **Soprano**: Channel 0
- **Alto**: Channel 1
- **Tenor**: Channel 2
- **Bass**: Channel 3

You can customize this mapping:

```python
midi = MidiCommunicator(channel_mapping={
    'soprano': 0,
    'alto': 1,
    'tenor': 2,
    'bass': 9  # Percussion channel
})
```

## MIDI Ports

The communicator will:
1. Use a specified port name if provided
2. Use the first available MIDI output port
3. Create a virtual MIDI port named "Figured Bass Realizer" if no ports exist

List available ports:

```python
from src.realization.midi_communicator import list_midi_ports
list_midi_ports()
```

## Features

- **Real-time playback**: Chords play with accurate timing based on BPM
- **Voice separation**: Each SATB voice on separate MIDI channel
- **Instrument selection**: Set General MIDI instruments per voice
- **Velocity control**: Adjust note velocity (dynamics)
- **Keyboard interrupt**: Press Ctrl+C to stop playback gracefully

## Integration with DAWs

The MIDI output can be routed to:
- **DAWs**: Ableton Live, Logic Pro, FL Studio, etc.
- **Software synths**: FluidSynth, Pianoteq, etc.
- **Hardware synths**: Via MIDI interface
- **Virtual MIDI routing**: IAC Driver (macOS), loopMIDI (Windows), ALSA (Linux)

## Example: Route to DAW

1. Create a virtual MIDI port (e.g., IAC Driver on macOS)
2. Configure your DAW to receive MIDI from that port
3. Run the script - it will send MIDI to the virtual port
4. Your DAW will receive the MIDI messages in real-time
