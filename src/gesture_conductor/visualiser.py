"""
Real-time visualization module for gesture conductor.
Displays hand tracking, beat detection, and musical parameters.
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import time


@dataclass
class VisualizationConfig:
    """Configuration for visualization settings."""
    
    # Window settings
    window_width: int = 1280
    window_height: int = 720
    fps_display: bool = True
    
    # Colors (BGR format)
    hand_color: Tuple[int, int, int] = (0, 255, 0)
    beat_color: Tuple[int, int, int] = (0, 0, 255)
    trail_color: Tuple[int, int, int] = (255, 255, 0)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    background_color: Tuple[int, int, int] = (0, 0, 0)
    
    # Hand tracking visualization
    draw_landmarks: bool = True
    draw_connections: bool = True
    landmark_radius: int = 5
    connection_thickness: int = 2
    
    # Trail visualization
    trail_length: int = 30
    trail_thickness: int = 2
    fade_trail: bool = True
    
    # Beat visualization
    beat_indicator_duration: float = 0.2  # seconds
    beat_circle_radius: int = 50
    beat_flash_intensity: float = 1.0
    
    # Info panel
    show_info_panel: bool = True
    info_panel_width: int = 300
    info_panel_alpha: float = 0.7
    
    # Debug visualization
    debug_mode: bool = False
    show_velocity_vectors: bool = False
    show_grid: bool = False


class Visualizer:
    """Main visualization class for gesture conductor."""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize visualizer.
        
        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()
        self.beat_timestamps: List[float] = []
        self.position_history: List[List[Tuple[float, float]]] = []
        self.frame_times: List[float] = []
        self.last_frame_time = time.time()
        
    def create_canvas(
        self,
        frame: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Create visualization canvas.
        
        Args:
            frame: Optional camera frame to use as background
            
        Returns:
            Canvas image
        """
        if frame is not None:
            # Resize frame to match window size
            canvas = cv2.resize(
                frame,
                (self.config.window_width, self.config.window_height)
            )
        else:
            # Create blank canvas
            canvas = np.full(
                (self.config.window_height, self.config.window_width, 3),
                self.config.background_color,
                dtype=np.uint8
            )
        
        if self.config.show_grid and self.config.debug_mode:
            self._draw_grid(canvas)
        
        return canvas
    
    def draw_hands(
        self,
        canvas: np.ndarray,
        hands: List[Any],
        hand_landmarks_list: Optional[Any] = None
    ) -> np.ndarray:
        """
        Draw hand landmarks and connections.

        Args:
            canvas: Image to draw on
            hands: List of detected hand positions (HandPosition objects)
            hand_landmarks_list: Optional MediaPipe HandLandmarkerResult or list of landmarks

        Returns:
            Canvas with hands drawn
        """
        if not hands:
            return canvas

        h, w = canvas.shape[:2]

        for i, hand in enumerate(hands):
            # Convert normalized coordinates to pixel coordinates
            x = int(hand.x * w)
            y = int(hand.y * h)

            # Draw main hand position (index finger tip)
            cv2.circle(
                canvas,
                (x, y),
                self.config.landmark_radius * 2,
                self.config.hand_color,
                -1
            )

            # Draw landmarks if available
            if hand_landmarks_list is not None:
                # Handle MediaPipe HandLandmarkerResult format
                if hasattr(hand_landmarks_list, 'hand_landmarks') and not isinstance(hand_landmarks_list, list):
                    if i < len(hand_landmarks_list.hand_landmarks):
                        self._draw_hand_landmarks(
                            canvas,
                            hand_landmarks_list.hand_landmarks[i],
                            w,
                            h
                        )
                # Handle list of landmarks
                elif isinstance(hand_landmarks_list, list) and i < len(hand_landmarks_list):
                    self._draw_hand_landmarks(
                        canvas,
                        hand_landmarks_list[i],
                        w,
                        h
                    )

            # Draw velocity vector if in debug mode
            if self.config.show_velocity_vectors and self.config.debug_mode:
                if hasattr(hand, 'velocity_y'):
                    self._draw_velocity_vector(
                        canvas,
                        (x, y),
                        (hand.velocity_x, hand.velocity_y),
                        w,
                        h
                    )

        return canvas
    
    def draw_trail(
        self,
        canvas: np.ndarray,
        positions: List[Tuple[float, float]],
        hand_index: int = 0
    ) -> np.ndarray:
        """
        Draw movement trail for hand.
        
        Args:
            canvas: Image to draw on
            positions: List of (x, y) positions in normalized coordinates
            hand_index: Index of hand to draw trail for
            
        Returns:
            Canvas with trail drawn
        """
        if len(positions) < 2:
            return canvas
        
        h, w = canvas.shape[:2]
        
        # Keep only recent positions
        recent_positions = positions[-self.config.trail_length:]
        
        # Draw trail segments
        for i in range(len(recent_positions) - 1):
            x1 = int(recent_positions[i][0] * w)
            y1 = int(recent_positions[i][1] * h)
            x2 = int(recent_positions[i + 1][0] * w)
            y2 = int(recent_positions[i + 1][1] * h)
            
            # Calculate fade factor
            if self.config.fade_trail:
                fade_factor = (i + 1) / len(recent_positions)
                color = tuple(int(c * fade_factor) for c in self.config.trail_color)
            else:
                color = self.config.trail_color
            
            cv2.line(
                canvas,
                (x1, y1),
                (x2, y2),
                color,
                self.config.trail_thickness
            )
        
        return canvas
    
    def draw_beats(
        self,
        canvas: np.ndarray,
        beats: List[Any]
    ) -> np.ndarray:
        """
        Draw beat indicators.
        
        Args:
            canvas: Image to draw on
            beats: List of detected beats
            
        Returns:
            Canvas with beats drawn
        """
        current_time = time.time()
        h, w = canvas.shape[:2]
        
        # Update beat timestamps
        self.beat_timestamps = [
            ts for ts in self.beat_timestamps
            if current_time - ts < self.config.beat_indicator_duration
        ]
        
        # Add new beats
        for beat in beats:
            if hasattr(beat, 'timestamp'):
                if beat.timestamp not in self.beat_timestamps:
                    self.beat_timestamps.append(beat.timestamp)
        
        # Draw beat indicators
        for ts in self.beat_timestamps:
            age = current_time - ts
            if age < self.config.beat_indicator_duration:
                # Calculate flash intensity
                intensity = 1.0 - (age / self.config.beat_indicator_duration)
                intensity *= self.config.beat_flash_intensity
                
                # Draw beat flash overlay
                overlay = canvas.copy()
                cv2.rectangle(
                    overlay,
                    (0, 0),
                    (w, h),
                    self.config.beat_color,
                    -1
                )
                cv2.addWeighted(
                    overlay,
                    intensity * 0.3,
                    canvas,
                    1 - intensity * 0.3,
                    0,
                    canvas
                )
        
        # Draw beat markers on positions
        for beat in beats:
            if hasattr(beat, 'position'):
                x = int(beat.position[0] * w)
                y = int(beat.position[1] * h)
                
                cv2.circle(
                    canvas,
                    (x, y),
                    self.config.beat_circle_radius,
                    self.config.beat_color,
                    3
                )
        
        return canvas
    
    def draw_info_panel(
        self,
        canvas: np.ndarray,
        info: Dict[str, Any]
    ) -> np.ndarray:
        """
        Draw information panel with statistics.
        
        Args:
            canvas: Image to draw on
            info: Dictionary of information to display
            
        Returns:
            Canvas with info panel drawn
        """
        if not self.config.show_info_panel:
            return canvas
        
        h, w = canvas.shape[:2]
        panel_w = self.config.info_panel_width
        
        # Create semi-transparent panel
        overlay = canvas.copy()
        cv2.rectangle(
            overlay,
            (w - panel_w, 0),
            (w, h),
            (40, 40, 40),
            -1
        )
        cv2.addWeighted(
            overlay,
            self.config.info_panel_alpha,
            canvas,
            1 - self.config.info_panel_alpha,
            0,
            canvas
        )
        
        # Draw panel border
        cv2.rectangle(
            canvas,
            (w - panel_w, 0),
            (w, h),
            (80, 80, 80),
            2
        )
        
        # Draw information text
        y_offset = 30
        line_height = 30

        # Title
        cv2.putText(
            canvas,
            "Gesture Conductor",
            (w - panel_w + 10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            self.config.text_color,
            2
        )

        y_offset = int(y_offset + line_height * 1.5)
        
        # Display metrics
        metrics = [
            ("Tempo", f"{info.get('tempo', 0):.1f} BPM"),
            ("Beats", str(info.get('beat_count', 0))),
            ("Articulation", f"{info.get('articulation', 0):.2f}"),
            ("Hands", str(info.get('num_hands', 0))),
        ]
        
        for label, value in metrics:
            # Label
            cv2.putText(
                canvas,
                f"{label}:",
                (w - panel_w + 10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1
            )
            
            # Value
            cv2.putText(
                canvas,
                value,
                (w - panel_w + 150, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.config.text_color,
                1
            )

            y_offset += line_height

        # FPS counter
        if self.config.fps_display:
            fps = self._calculate_fps()
            y_offset = int(y_offset + line_height * 0.5)
            cv2.putText(
                canvas,
                f"FPS: {fps:.1f}",
                (w - panel_w + 10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (100, 255, 100),
                1
            )
        
        # Controls help
        y_offset = h - 150
        cv2.putText(
            canvas,
            "Controls:",
            (w - panel_w + 10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )
        
        y_offset += line_height
        controls = [
            "SPACE - Start/Stop",
            "R - Reset",
            "S - Save",
            "Q - Quit"
        ]
        
        for control in controls:
            cv2.putText(
                canvas,
                control,
                (w - panel_w + 10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (150, 150, 150),
                1
            )
            y_offset = int(y_offset + line_height * 0.8)
        
        return canvas
    
    def draw_tempo_graph(
        self,
        canvas: np.ndarray,
        tempo_history: List[float],
        position: Tuple[int, int] = (50, 50),
        size: Tuple[int, int] = (200, 100)
    ) -> np.ndarray:
        """
        Draw tempo graph visualization.
        
        Args:
            canvas: Image to draw on
            tempo_history: List of tempo values over time
            position: (x, y) position of graph
            size: (width, height) of graph
            
        Returns:
            Canvas with tempo graph drawn
        """
        if len(tempo_history) < 2:
            return canvas
        
        x, y = position
        w, h = size
        
        # Draw graph background
        overlay = canvas.copy()
        cv2.rectangle(
            overlay,
            (x, y),
            (x + w, y + h),
            (40, 40, 40),
            -1
        )
        cv2.addWeighted(
            overlay,
            0.7,
            canvas,
            0.3,
            0,
            canvas
        )
        
        # Draw border
        cv2.rectangle(
            canvas,
            (x, y),
            (x + w, y + h),
            (80, 80, 80),
            1
        )
        
        # Draw graph title
        cv2.putText(
            canvas,
            "Tempo",
            (x + 5, y + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            self.config.text_color,
            1
        )
        
        # Normalize tempo values
        recent_tempos = tempo_history[-50:]  # Last 50 values
        if recent_tempos:
            min_tempo = max(30, min(recent_tempos) - 10)
            max_tempo = min(240, max(recent_tempos) + 10)
            
            # Draw tempo line
            points = []
            for i, tempo in enumerate(recent_tempos):
                px = x + int((i / len(recent_tempos)) * w)
                py = y + h - int(((tempo - min_tempo) / (max_tempo - min_tempo)) * (h - 20))
                points.append((px, py))
            
            # Draw line segments
            for i in range(len(points) - 1):
                cv2.line(
                    canvas,
                    points[i],
                    points[i + 1],
                    (100, 200, 255),
                    2
                )
            
            # Draw current tempo value
            if recent_tempos:
                cv2.putText(
                    canvas,
                    f"{recent_tempos[-1]:.1f}",
                    (x + w - 50, y + h - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (100, 200, 255),
                    1
                )
        
        return canvas
    
    def _draw_hand_landmarks(
        self,
        canvas: np.ndarray,
        landmarks: Any,
        width: int,
        height: int
    ) -> None:
        """
        Draw hand landmarks and connections.

        Args:
            canvas: Image to draw on
            landmarks: MediaPipe hand landmarks (list or NormalizedLandmarkList)
            width: Image width
            height: Image height
        """
        # MediaPipe hand connections
        HAND_CONNECTIONS = [
            # Thumb
            (0, 1), (1, 2), (2, 3), (3, 4),
            # Index finger
            (0, 5), (5, 6), (6, 7), (7, 8),
            # Middle finger
            (0, 9), (9, 10), (10, 11), (11, 12),
            # Ring finger
            (0, 13), (13, 14), (14, 15), (15, 16),
            # Pinky
            (0, 17), (17, 18), (18, 19), (19, 20),
            # Palm
            (5, 9), (9, 13), (13, 17)
        ]

        # Determine if landmarks is a list or has .landmark attribute
        if isinstance(landmarks, list):
            landmark_list = landmarks
        elif hasattr(landmarks, 'landmark'):
            landmark_list = landmarks.landmark
        else:
            return

        # Draw connections
        if self.config.draw_connections:
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection

                if start_idx < len(landmark_list) and end_idx < len(landmark_list):
                    start = landmark_list[start_idx]
                    end = landmark_list[end_idx]

                    start_x = int(start.x * width)
                    start_y = int(start.y * height)
                    end_x = int(end.x * width)
                    end_y = int(end.y * height)

                    cv2.line(
                        canvas,
                        (start_x, start_y),
                        (end_x, end_y),
                        self.config.hand_color,
                        self.config.connection_thickness
                    )

        # Draw landmarks
        if self.config.draw_landmarks:
            for landmark in landmark_list:
                x = int(landmark.x * width)
                y = int(landmark.y * height)

                cv2.circle(
                    canvas,
                    (x, y),
                    self.config.landmark_radius,
                    self.config.hand_color,
                    -1
                )

                # Draw landmark border
                cv2.circle(
                    canvas,
                    (x, y),
                    self.config.landmark_radius + 1,
                    (0, 0, 0),
                    1
                )
    
    def _draw_velocity_vector(
        self,
        canvas: np.ndarray,
        position: Tuple[int, int],
        velocity: Tuple[float, float],
        width: int,
        height: int
    ) -> None:
        """
        Draw velocity vector for debugging.
        
        Args:
            canvas: Image to draw on
            position: (x, y) pixel position
            velocity: (vx, vy) velocity vector (normalized)
            width: Image width
            height: Image height
        """
        x, y = position
        vx, vy = velocity
        
        # Scale velocity for visualization
        scale = 100.0
        end_x = int(x + vx * scale)
        end_y = int(y + vy * scale)
        
        # Draw velocity arrow
        cv2.arrowedLine(
            canvas,
            (x, y),
            (end_x, end_y),
            (255, 0, 255),
            2,
            tipLength=0.3
        )
        
        # Draw velocity magnitude
        magnitude = np.sqrt(vx**2 + vy**2)
        cv2.putText(
            canvas,
            f"{magnitude:.2f}",
            (end_x + 5, end_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 0, 255),
            1
        )
    
    def _draw_grid(self, canvas: np.ndarray) -> None:
        """
        Draw reference grid for debugging.
        
        Args:
            canvas: Image to draw on
        """
        h, w = canvas.shape[:2]
        grid_spacing = 50
        grid_color = (60, 60, 60)
        
        # Draw vertical lines
        for x in range(0, w, grid_spacing):
            cv2.line(canvas, (x, 0), (x, h), grid_color, 1)
        
        # Draw horizontal lines
        for y in range(0, h, grid_spacing):
            cv2.line(canvas, (0, y), (w, y), grid_color, 1)
        
        # Draw center crosshair
        center_x, center_y = w // 2, h // 2
        cv2.line(
            canvas,
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            (100, 100, 100),
            2
        )
        cv2.line(
            canvas,
            (center_x, center_y - 20),
            (center_x, center_y + 20),
            (100, 100, 100),
            2
        )
    
    def _calculate_fps(self) -> float:
        """
        Calculate current FPS.
        
        Returns:
            Current frames per second
        """
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # Keep only last second of frame times
        self.frame_times = [
            t for t in self.frame_times
            if current_time - t < 1.0
        ]
        
        if len(self.frame_times) > 1:
            return len(self.frame_times)
        return 0.0
    
    def render_frame(
        self,
        frame: Optional[np.ndarray],
        hands: List[Any],
        beats: List[Any],
        info: Dict[str, Any],
        position_history: Optional[List[Tuple[float, float]]] = None,
        tempo_history: Optional[List[float]] = None,
        hand_landmarks_list: Optional[List[Any]] = None
    ) -> np.ndarray:
        """
        Render complete visualization frame.
        
        Args:
            frame: Camera frame
            hands: List of detected hands
            beats: List of detected beats
            info: Information dictionary for display
            position_history: Optional position history for trails
            tempo_history: Optional tempo history for graph
            hand_landmarks_list: Optional MediaPipe landmarks
            
        Returns:
            Rendered frame
        """
        # Create canvas
        canvas = self.create_canvas(frame)
        
        # Draw trail
        if position_history and len(position_history) > 0:
            canvas = self.draw_trail(canvas, position_history)
        
        # Draw hands
        canvas = self.draw_hands(canvas, hands, hand_landmarks_list)
        
        # Draw beats
        canvas = self.draw_beats(canvas, beats)
        
        # Draw tempo graph
        if tempo_history and len(tempo_history) > 1 and not self.config.show_info_panel:
            canvas = self.draw_tempo_graph(
                canvas,
                tempo_history,
                position=(50, 50),
                size=(200, 100)
            )
        
        # Draw info panel
        canvas = self.draw_info_panel(canvas, info)
        
        # Update frame time
        self.last_frame_time = time.time()
        
        return canvas
    
    def draw_recording_indicator(
        self,
        canvas: np.ndarray,
        is_recording: bool = True
    ) -> np.ndarray:
        """
        Draw recording indicator.
        
        Args:
            canvas: Image to draw on
            is_recording: Whether currently recording
            
        Returns:
            Canvas with recording indicator
        """
        if not is_recording:
            return canvas
        
        # Blinking effect
        blink = int(time.time() * 2) % 2 == 0
        
        if blink:
            # Draw red circle
            cv2.circle(
                canvas,
                (30, 30),
                10,
                (0, 0, 255),
                -1
            )
            
            # Draw "REC" text
            cv2.putText(
                canvas,
                "REC",
                (50, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )
        
        return canvas
    
    def draw_status_message(
        self,
        canvas: np.ndarray,
        message: str,
        duration: float = 2.0,
        message_type: str = "info"
    ) -> np.ndarray:
        """
        Draw temporary status message.
        
        Args:
            canvas: Image to draw on
            message: Message text
            duration: How long to display (seconds)
            message_type: Type of message ('info', 'success', 'warning', 'error')
            
        Returns:
            Canvas with status message
        """
        h, w = canvas.shape[:2]
        
        # Choose color based on message type
        colors = {
            'info': (255, 255, 255),
            'success': (0, 255, 0),
            'warning': (0, 255, 255),
            'error': (0, 0, 255)
        }
        color = colors.get(message_type, (255, 255, 255))
        
        # Calculate text size
        font_scale = 0.8
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(
            message,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            thickness
        )
        
        # Draw background
        padding = 20
        bg_x1 = (w - text_width) // 2 - padding
        bg_y1 = h - 100 - padding
        bg_x2 = (w + text_width) // 2 + padding
        bg_y2 = h - 100 + text_height + padding
        
        overlay = canvas.copy()
        cv2.rectangle(
            overlay,
            (bg_x1, bg_y1),
            (bg_x2, bg_y2),
            (40, 40, 40),
            -1
        )
        cv2.addWeighted(overlay, 0.8, canvas, 0.2, 0, canvas)
        
        # Draw border
        cv2.rectangle(
            canvas,
            (bg_x1, bg_y1),
            (bg_x2, bg_y2),
            color,
            2
        )
        
        # Draw text
        text_x = (w - text_width) // 2
        text_y = h - 100 + text_height
        
        cv2.putText(
            canvas,
            message,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness
        )
        
        return canvas
    
    def cleanup(self) -> None:
        """Clean up resources."""
        cv2.destroyAllWindows()


def create_default_visualizer() -> Visualizer:
    """
    Create visualizer with default configuration.
    
    Returns:
        Configured Visualizer instance
    """
    config = VisualizationConfig(
        window_width=1280,
        window_height=720,
        fps_display=True,
        trail_length=30,
        beat_indicator_duration=0.2,
        show_info_panel=True
    )
    return Visualizer(config)
