# src/gesture_conductor/detector.py
"""Core gesture detection using MediaPipe."""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class HandLandmark(Enum):
    """Hand landmark indices."""
    WRIST = 0
    THUMB_TIP = 4
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_TIP = 16
    PINKY_TIP = 20


@dataclass
class HandPosition:
    """Hand position data."""
    timestamp: float
    x: float
    y: float
    z: float
    visibility: float


class GestureDetector:
    """Detects hand gestures using MediaPipe."""

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
        max_num_hands: int = 1,
        model_path: Optional[str] = None
    ):
        """
        Initialize the gesture detector.

        Args:
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
            max_num_hands: Maximum number of hands to detect
            model_path: Optional path to custom model file (defaults to models/hand_landmarker.task)
        """
        # Import MediaPipe task modules
        self.BaseOptions = mp.tasks.BaseOptions
        self.HandLandmarker = mp.tasks.vision.HandLandmarker
        self.HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        self.HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
        self.VisionRunningMode = mp.tasks.vision.RunningMode

        self.position_history: List[HandPosition] = []
        self.last_result: Optional[mp.tasks.vision.HandLandmarkerResult] = None # type: ignore
        self.last_timestamp_ms: int = 0

        # Find model file if not specified
        if model_path is None:
            # Try to find the model relative to the project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            model_path = str(project_root / "models" / "hand_landmarker.task")

            if not Path(model_path).exists():
                raise FileNotFoundError(
                    f"Model file not found at {model_path}. "
                    "Please provide a valid model_path or ensure models/hand_landmarker.task exists."
                )

        # Create options
        base_options = self.BaseOptions(model_asset_path=model_path)

        options = self.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            result_callback=self._result_callback
        )

        self.landmarker = self.HandLandmarker.create_from_options(options)

    def _result_callback(
        self,
        result: mp.tasks.vision.HandLandmarkerResult, # type: ignore
        output_image: mp.Image,
        timestamp_ms: int
    ):
        """
        Callback function for processing hand landmarker results.

        Args:
            result: HandLandmarkerResult containing detected landmarks
            output_image: Processed image
            timestamp_ms: Frame timestamp in milliseconds
        """
        self.last_result = result
        self.last_timestamp_ms = timestamp_ms

        # Extract and store hand position if detected
        if result.hand_landmarks:
            # Get the first hand
            hand_landmarks = result.hand_landmarks[0]

            # Extract index finger tip position
            index_tip = hand_landmarks[HandLandmark.INDEX_FINGER_TIP.value]

            position = HandPosition(
                timestamp=timestamp_ms / 1000.0,  # Convert to seconds
                x=index_tip.x,
                y=index_tip.y,
                z=index_tip.z,
                visibility=index_tip.visibility if hasattr(index_tip, 'visibility') else 1.0
            )

            self.position_history.append(position)

    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: float
    ) -> Optional[HandPosition]:
        """
        Process a single frame to detect hand position.

        Args:
            frame: Input BGR image frame
            timestamp: Current timestamp in seconds

        Returns:
            HandPosition if hand detected, None otherwise
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Convert timestamp to milliseconds
        timestamp_ms = int(timestamp * 1000)

        # Process asynchronously
        self.landmarker.detect_async(mp_image, timestamp_ms)

        # Return the most recent position if available
        if self.position_history and self.position_history[-1].timestamp <= timestamp:
            return self.position_history[-1]

        return None

    def draw_landmarks(
        self,
        frame: np.ndarray
    ) -> np.ndarray:
        """
        Draw hand landmarks on the frame using the last detection result.

        Args:
            frame: Input BGR image frame

        Returns:
            Frame with landmarks drawn
        """
        annotated_frame = frame.copy()

        if self.last_result and self.last_result.hand_landmarks:
            for hand_landmarks in self.last_result.hand_landmarks:
                # Convert normalized landmarks to pixel coordinates
                height, width = frame.shape[:2]

                # Draw connections
                for connection in mp.solutions.hands.HAND_CONNECTIONS: # type: ignore
                    start_idx, end_idx = connection
                    start = hand_landmarks[start_idx]
                    end = hand_landmarks[end_idx]

                    start_point = (int(start.x * width), int(start.y * height))
                    end_point = (int(end.x * width), int(end.y * height))

                    cv2.line(annotated_frame, start_point, end_point, (0, 255, 0), 2)

                # Draw landmarks
                for landmark in hand_landmarks:
                    point = (int(landmark.x * width), int(landmark.y * height))
                    cv2.circle(annotated_frame, point, 5, (255, 0, 0), -1)

        return annotated_frame

    def get_position_history(
        self,
        window_seconds: Optional[float] = None
    ) -> List[HandPosition]:
        """
        Get position history, optionally filtered by time window.

        Args:
            window_seconds: Time window in seconds (None for all history)

        Returns:
            List of HandPosition objects
        """
        if window_seconds is None:
            return self.position_history.copy()

        if not self.position_history:
            return []

        current_time = self.position_history[-1].timestamp
        cutoff_time = current_time - window_seconds

        return [
            pos for pos in self.position_history
            if pos.timestamp >= cutoff_time
        ]

    def clear_history(self):
        """Clear position history."""
        self.position_history.clear()

    def close(self):
        """Cleanup resources."""
        if hasattr(self, 'landmarker'):
            self.landmarker.close()

    def __del__(self):
        """Cleanup resources."""
        self.close()
