"""Gesture Conductor - Main Application."""

import cv2
import time
from src.gesture_conductor.conductor import ConductorGestureAnalyzer
from src.gesture_conductor.visualiser import Visualizer, VisualizationConfig


def main():
    """Run the gesture conductor application with full visualization."""
    print("=" * 60)
    print("Gesture Conductor - Real-time Conducting Analysis")
    print("=" * 60)
    print("\nInitializing...")

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

    # Open webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    print("\nWebcam opened successfully")
    print("\nControls:")
    print("  SPACE - Pause/Resume")
    print("  R     - Reset analyzer")
    print("  C     - Clear history")
    print("  Q     - Quit")
    print("\nStarting visualization...\n")

    start_time = time.time()
    frame_count = 0
    paused = False

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

            if not paused:
                # Analyze the frame for conducting gestures
                position, new_beats, state = conductor.analyze_frame(frame, current_time)

                # Give the async callback time to process
                time.sleep(0.005)

                # Update tempo history
                if state.tempo_bpm:
                    tempo_history.append(state.tempo_bpm)
                    # Keep only recent history
                    if len(tempo_history) > 100:
                        tempo_history.pop(0)

                # Update position trail
                if position:
                    position_trail.append((position.x, position.y))
                    # Keep only recent trail
                    if len(position_trail) > viz_config.trail_length:
                        position_trail.pop(0)

                # Print beat detection info
                if new_beats:
                    for beat in new_beats:
                        print(f"Beat! Direction: {beat.direction.name:8s} | "
                              f"Velocity: {beat.velocity:.3f} | "
                              f"Articulation: {beat.articulation:.2f} | "
                              f"Time: {current_time:.2f}s")

            # Prepare visualization data
            hands = [position] if position else []

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

            # Add conducting status indicator
            if state.is_conducting:
                cv2.putText(
                    canvas,
                    "CONDUCTING",
                    (50, 50),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1.2,
                    (0, 255, 0),
                    3
                )
            else:
                cv2.putText(
                    canvas,
                    "Not Conducting",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (100, 100, 100),
                    2
                )

            # Add pause indicator
            if paused:
                canvas = visualizer.draw_status_message(
                    canvas,
                    "PAUSED",
                    message_type="warning"
                )

            # Show the frame
            cv2.imshow('Gesture Conductor', canvas)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord('r'):
                conductor.reset()
                tempo_history.clear()
                position_trail.clear()
                print("Analyzer reset")
            elif key == ord('c'):
                conductor.gesture_detector.clear_history()
                position_trail.clear()
                print("History cleared")
            elif key == ord(' '):
                paused = not paused
                print("Paused" if paused else "Resumed")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Cleanup
        print("\nCleaning up...")
        cap.release()
        visualizer.cleanup()
        conductor.gesture_detector.close()

        # Print final statistics
        state = conductor.get_state()
        musical_params = conductor.get_musical_parameters()

        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)

        print("\nPerformance:")
        print(f"  Total frames:     {frame_count}")
        print(f"  Duration:         {current_time:.2f} seconds")
        print(f"  Average FPS:      {frame_count / current_time:.1f}" if current_time > 0 else "  Average FPS: N/A")

        print("\nConducting Statistics:")
        print(f"  Total beats:      {state.beats_detected}")
        print(f"  Final tempo:      {state.tempo_bpm:.1f} BPM" if state.tempo_bpm else "  Final tempo: N/A")
        print(f"  Avg velocity:     {state.average_velocity:.3f}")

        print("\nMusical Parameters:")
        print(f"  Articulation:     {musical_params['articulation']:.2f} "
              f"({'Staccato' if musical_params['articulation'] > 0.6 else 'Legato' if musical_params['articulation'] < 0.4 else 'Normal'})")
        print(f"  Note duration:    {musical_params['note_duration_factor']:.2f}x")
        print(f"  Attack time:      {musical_params['attack_time_ms']:.1f}ms")
        print(f"  Release time:     {musical_params['release_time_ms']:.1f}ms")
        print(f"  Dynamics:         {musical_params['dynamics']:.2f}")

        print("\n" + "=" * 60)
        print("Thank you for using Gesture Conductor!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
