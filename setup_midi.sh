#!/bin/bash
# Setup script for MIDI dependencies

echo "Setting up MIDI environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing MIDI dependencies..."
pip install mido python-rtmidi

echo ""
echo "Setup complete!"
echo ""
echo "To use the MIDI functionality:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the script: python scripts/play_figured_bass_midi.py"
echo ""
