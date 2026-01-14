"""Gesture Conductor with MIDI Figured Bass - Integrated Application."""

import cv2
import time
import sys
from pathlib import Path

from src.gesture_conductor.conductor import ConductorGestureAnalyzer
from src.gesture_conductor.visualiser import Visualizer, VisualizationConfig
from src.realization.lilypond_parser import parse_lilypond_file
from src.realization.generator import FiguredBassRealizer
from src.realization.midi_communicator import MidiCommunicator
from src.realization.adaptive_midi_player import AdaptiveMidiPlayer


def midi_to_note_name(midi_note: int) -> str:
    """Convert MIDI note number to note name."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{note_names[note_index]}{octave}"


def main():
    """Run the integrated gesture conductor with MIDI figured bass."""
    print("=" * 70)
    print("Gesture Conductor with MIDI Figured Bass")
    print("=" * 70)
    print("\nInitializing...")

    # Get figured bass file
    if len(sys.argv) > 1:
        figured_bass_file = sys.argv[1]
    else:
        figured_bass_file = Path(__file__).parent / "examples" / "figured_bass_long.ily"
    
    print(f"\nLoading figured bass: {figured_bass_file}")
    
    # Parse and realize figured bass
    try:
        symbols = parse_lilypond_file(str(figured_bass_file))
        print(f"Parsed {len(symbols)} figured bass symbols")
        
        realizer = FiguredBassRealizer(key="C", mode="major")
        chords = realizer.realize_figured_bass(symbols, style="strict")
        print(f"Realized {len(chords)} chords")
    except Exception as e:
        print(f"Error loading figured bass: {e}")
        return 1

    # Create visualization configuration
    viz_config = VisualizationConfig(
        window_width=1280,
        window_height=720,
        fps_display=True,
        trail_length=50,
        trail_thickness=3,
        fade_trail=True,
        beat_indicator_duration=0.3,
        beat_flash_intensity=0.8,
        show_info_panel=True,
        info_panel_width=320,
        hand_color=(0, 255, 0),
        beat_color=(0, 255, 255),
        trail_color=(255, 100, 255),
        landmark_radius=4,
        connection_thickness=2
    )

    # Initialize components
    visualizer = Visualizer(viz_config)
    conductor = ConductorGestureAnalyzer(history_window=2.5)
    
    # Initialize MIDI
    print("\nInitializing MIDI...")
    midi = MidiCommunicator()
    midi.open()
    
    # Set instruments (all piano for now)
    midi.set_instruments({
        'soprano': 0,  # Acoustic Grand Piano
        'alto': 0,
        'tenor': 0,
        'bass': 0
    })
    
    # Create tempo-adaptive player
    player = AdaptiveMidiPlayer(
        chords=chords,
        midi_communicator=midi,
        velocity_base=70,
        velocity_range=50,
        default_bpm=120.0,
        loop=True
    )
    
    # Setup callbacks
    def on_chord_change(index, chord):
        """Called when chord changes."""
        print(f"Chord {index + 1}/{len(chords)}: "
              f"S={midi_to_note_name(chord.soprano)} "
              f"A={midi_to_note_name(chord.alto)} "
              f"T={midi_to_note_name(chord.tenor)} "
              f"B={midi_to_note_name(chord.bass)}")
    
    def on_progression_complete():
        """Called when progression completes (loops)."""
        print("--- Progression complete, looping ---")
    
    player.on_chord_change = on_chord_change
    player.on_progression_complete = on_progression_complete

    # Open webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        midi.close()
        return 1

    print("\nWebcam opened successfully")
    print("\nControls:")
    print("  SPACE - Start/Pause playback")
    print("  R     - Reset to beginning")
    print("  C     - Clear gesture history")
    print("  Q     - Quit")
    print("\nConduct to control the tempo!")
    print("The playback will adapt to your conducting speed in real-time.\n")

    start_time = time.time()
    frame_count = 0
    paused = True  # Start paused

    # History tracking for visualization
    tempo_history = []
    position_trail = []

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Error: Could not read frame")
                break

            # Get current timestamp
            current_time = time.time() - start_time
            frame_count += 1

            # Analyze the frame for conducting gestures
            position, new_beats, state = conductor.analyze_frame(frame, current_time)

            # Update tempo history
            if state.tempo_bpm:
                tempo_history.append(state.tempo_bpm)
                if len(tempo_history) > 100:
                    tempo_history.pop(0)

            # Update position trail
            if position:
                position_trail.append((position.x, position.y))
                if len(position_trail) > viz_config.trail_length:
                    position_trail.pop(0)

            # Update player with current conductor state (continuous adaptation)
            if not paused:
                musical_params = conductor.get_musical_parameters()
                player.update_conductor_state(
                    tempo_bpm=state.tempo_bpm,
                    dynamics=musical_params.get('dynamics', 0.5),
                    articulation=musical_params.get('articulation', 0.5)
                )

            # Prepare visualization data
            hands = [position] if position else []

            # Get playback progress
            current_chord, total_chords = player.get_progress()

            # Prepare info dictionary for display
            info = {
                'tempo': state.tempo_bpm if state.tempo_bpm else 0,
                'beat_count': state.beats_detected,
                'articulation': state.articulation,
                'num_hands': 1 if position else 0,
                'velocity': state.average_velocity,
                'conducting': state.is_conducting
            }

            # Render the complete visualization
            canvas = visualizer.render_frame(
                frame=frame,
                hands=hands,
                beats=new_beats if not paused else [],
                info=info,
                position_history=position_trail,
                tempo_history=tempo_history,
                hand_landmarks_list=conductor.gesture_detector.last_result
            )

            # Add playback status
            status_y = 50
            if not paused and player.is_playing:
                cv2.putText(
                    canvas,
                    f"PLAYING: Chord {current_chord}/{total_chords}",
                    (50, status_y),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.0,
                    (0, 255, 0),
                    2
                )
            elif paused:
                cv2.putText(
                    canvas,
                    "PAUSED - Press SPACE to start",
                    (50, status_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (100, 100, 255),
                    2
                )
            
            # Add conducting status and tempo
            if state.is_conducting and not paused:
                tempo_display = f"{state.tempo_bpm:.0f} BPM" if state.tempo_bpm else "-- BPM"
                cv2.putText(
                    canvas,
                    f"Conducting at {tempo_display}",
                    (50, status_y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

            # Show the frame
            cv2.imshow('Gesture Conductor + MIDI', canvas)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord('r'):
                player.reset()
                conductor.reset()
                tempo_history.clear()
                position_trail.clear()
                print("Reset to beginning")
            elif key == ord('c'):
                conductor.gesture_detector.clear_history()
                position_trail.clear()
                print("Gesture history cleared")
            elif key == ord(' '):
                paused = not paused
                if paused:
                    player.pause()
                    print("Paused")
                else:
                    player.start()
                    print("Playing - conduct to advance chords!")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Cleanup
        print("\nCleaning up...")
        player.cleanup()
        cap.release()
        visualizer.cleanup()
        conductor.gesture_detector.close()

        # Print final statistics
        state = conductor.get_state()
        current_chord, total_chords = player.get_progress()

        print("\n" + "=" * 70)
        print("Session Summary")
        print("=" * 70)

        print("\nPerformance:")
        print(f"  Total frames:     {frame_count}")
        print(f"  Duration:         {current_time:.2f} seconds")
        print(f"  Average FPS:      {frame_count / current_time:.1f}" if current_time > 0 else "  Average FPS: N/A")

        print("\nConducting Statistics:")
        print(f"  Total beats:      {state.beats_detected}")
        print(f"  Final tempo:      {state.tempo_bpm:.1f} BPM" if state.tempo_bpm else "  Final tempo: N/A")
        print(f"  Avg velocity:     {state.average_velocity:.3f}")

        print("\nPlayback Statistics:")
        print(f"  Chords played:    {current_chord}/{total_chords}")
        print(f"  Progress:         {(current_chord/total_chords)*100:.1f}%")

        print("\n" + "=" * 70)
        print("Thank you for using Gesture Conductor + MIDI!")
        print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
