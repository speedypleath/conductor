# src/gesture_conductor/beat_detector.py
"""Beat detection from gesture data."""

import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from scipy.signal import find_peaks
from enum import Enum


class Direction(Enum):
    """Movement direction."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


@dataclass
class BeatEvent:
    """Represents a detected beat."""
    timestamp: float
    position: Tuple[float, float, float]  # x, y, z
    velocity: float
    acceleration: float
    direction: Direction
    tempo_bpm: Optional[float] = None
    articulation: float = 0.5  # 0.0 (smooth) to 1.0 (abrupt)


class BeatDetector:
    """Detects beats from hand position data."""
    
    def __init__(
        self,
        min_beat_distance: float = 0.25,  # seconds - reduced for faster beats
        velocity_threshold: float = 0.5,  # reduced for better sensitivity
        acceleration_threshold: float = 40.0,
        use_downbeat: bool = True,
        peak_prominence: float = 0.05  # reduced for better detection
    ):
        """
        Initialize beat detector.

        Args:
            min_beat_distance: Minimum time between beats in seconds
            velocity_threshold: Minimum velocity to consider as beat
            acceleration_threshold: Threshold for articulation detection
            use_downbeat: If True, detect beats on downward motion
            peak_prominence: Minimum prominence for peak detection
        """
        self.min_beat_distance = min_beat_distance
        self.velocity_threshold = velocity_threshold
        self.acceleration_threshold = acceleration_threshold
        self.use_downbeat = use_downbeat
        self.peak_prominence = peak_prominence

        self.beat_history: List[BeatEvent] = []
        self.last_beat_time: Optional[float] = None
        self._last_processed_timestamp: float = 0.0
        
    def detect_beats(
        self,
        positions: List,
        use_downbeat: Optional[bool] = None
    ) -> List[BeatEvent]:
        """
        Detect beats from position history.
        
        Args:
            positions: List of HandPosition objects
            use_downbeat: If True, detect beats on downward motion (overrides init)
            
        Returns:
            List of detected BeatEvent objects
        """
        if len(positions) < 3:
            return []
        
        if use_downbeat is None:
            use_downbeat = self.use_downbeat
        
        # Extract data arrays
        timestamps = np.array([p.timestamp for p in positions])
        y_positions = np.array([p.y for p in positions])
        x_positions = np.array([p.x for p in positions])
        z_positions = np.array([p.z for p in positions])
        
        # Calculate time differences
        dt = np.diff(timestamps)
        if len(dt) == 0 or np.min(dt) <= 0:
            return []
        
        # Calculate velocity (first derivative)
        dy = np.diff(y_positions)
        dx = np.diff(x_positions)
        dz = np.diff(z_positions)
        
        velocities_y = dy / dt
        velocities_x = dx / dt
        velocities_z = dz / dt
        
        # Calculate magnitude of velocity
        velocity_magnitudes = np.sqrt(
            velocities_x**2 + velocities_y**2 + velocities_z**2
        )
        
        # Calculate acceleration (second derivative)
        if len(velocities_y) < 2:
            return []
        
        accelerations_y = np.diff(velocities_y) / dt[:-1]
        acceleration_magnitudes = np.abs(accelerations_y)
        
        # Pad arrays to match original length
        velocities_y = np.concatenate([[0], velocities_y])
        velocities_x = np.concatenate([[0], velocities_x])
        velocity_magnitudes = np.concatenate([[0], velocity_magnitudes])
        acceleration_magnitudes = np.concatenate([[0, 0], acceleration_magnitudes])
        
        beats = []

        # Find peaks in vertical position (beats are typically at extrema)
        min_samples = max(1, int(self.min_beat_distance / np.mean(dt)))

        if use_downbeat:
            # For downbeat: Find valleys (lowest points) where finger reaches bottom
            # In image coordinates, higher y = lower on screen, so we want peaks in y
            peaks, properties = find_peaks(
                y_positions,
                distance=min_samples,
                prominence=self.peak_prominence
            )
        else:
            # For upbeat: Find peaks (highest points) where finger reaches top
            peaks, properties = find_peaks(
                -y_positions,
                distance=min_samples,
                prominence=self.peak_prominence
            )

        # Alternative: detect velocity sign changes (better for ictus point)
        # Find where velocity changes from positive (down) to negative (up)
        velocity_sign_changes = []
        for i in range(1, len(velocities_y)):
            # For downbeat, look for transition from moving down (positive) to moving up (negative)
            if use_downbeat:
                if velocities_y[i-1] > 0.05 and velocities_y[i] < -0.05:
                    velocity_sign_changes.append(i)
            else:
                # For upbeat, look for transition from moving up (negative) to moving down (positive)
                if velocities_y[i-1] < -0.05 and velocities_y[i] > 0.05:
                    velocity_sign_changes.append(i)

        # Combine both methods: prefer velocity sign changes, but fall back to peaks
        beat_candidates = set()

        # Add velocity sign changes as primary candidates
        for idx in velocity_sign_changes:
            beat_candidates.add(idx)

        # Add peaks as additional candidates
        for idx in peaks:
            beat_candidates.add(idx)

        # Process all candidates
        for peak_idx in sorted(beat_candidates):
            if peak_idx >= len(positions):
                continue

            pos = positions[peak_idx]

            # Only process new beats
            if pos.timestamp <= self._last_processed_timestamp:
                continue

            velocity = velocity_magnitudes[peak_idx]
            velocity_x = velocities_x[peak_idx]
            acceleration = float(acceleration_magnitudes[peak_idx]) if peak_idx < len(acceleration_magnitudes) else 0.0

            # Determine direction
            direction = self._get_direction(
                float(velocities_y[peak_idx]) if peak_idx < len(velocities_y) else 0.0,
                float(velocity_x)
            )

            # Calculate articulation (0.0 = smooth, 1.0 = abrupt)
            articulation = self._calculate_articulation(
                float(acceleration),
                float(velocity)
            )

            is_velocity_change = peak_idx in velocity_sign_changes
            has_sufficient_velocity = velocity >= self.velocity_threshold
            
            # pretty hacky way to ensure some y movement, should only check distance between frames from last beat
            y_movement = max(y_positions) - min(y_positions)
            
            if (is_velocity_change or has_sufficient_velocity) and y_movement >= 0.2:
                print(y_positions)
                # Check minimum beat distance
                if self.last_beat_time is None or \
                   (pos.timestamp - self.last_beat_time) >= self.min_beat_distance:

                    beat = BeatEvent(
                        timestamp=pos.timestamp,
                        position=(pos.x, pos.y, pos.z),
                        velocity=float(velocity),
                        acceleration=float(acceleration),
                        direction=direction,
                        articulation=articulation
                    )

                    beats.append(beat)
                    self.last_beat_time = pos.timestamp
        
        # Calculate tempo for each beat based on previous beat
        if beats:
            for i in range(len(beats)):
                if i > 0:
                    time_diff = beats[i].timestamp - beats[i-1].timestamp
                    bpm = 60.0 / time_diff
                    # Clamp to reasonable range
                    bpm = np.clip(bpm, 30, 240)
                    beats[i].tempo_bpm = float(bpm)
                elif len(self.beat_history) > 0:
                    # Use last beat from history
                    time_diff = beats[i].timestamp - self.beat_history[-1].timestamp
                    if time_diff > 0:
                        bpm = 60.0 / time_diff
                        bpm = np.clip(bpm, 30, 240)
                        beats[i].tempo_bpm = float(bpm)
        
        # Add to history
        self.beat_history.extend(beats)
        
        # Update last processed timestamp
        if positions:
            self._last_processed_timestamp = max(
                self._last_processed_timestamp,
                positions[-1].timestamp
            )
        
        return beats
    
    def _get_direction(
        self,
        vertical_velocity: float,
        horizontal_velocity: float
    ) -> Direction:
        """
        Determine primary movement direction.
        
        Args:
            vertical_velocity: Velocity in vertical direction (positive = down)
            horizontal_velocity: Velocity in horizontal direction (positive = right)
            
        Returns:
            Direction enum
        """
        v_threshold = 0.1
        h_threshold = 0.1
        
        abs_v = abs(vertical_velocity)
        abs_h = abs(horizontal_velocity)
        
        # Vertical movement dominates
        if abs_v > abs_h and abs_v > v_threshold:
            # In image coordinates, positive y is down
            return Direction.DOWN if vertical_velocity > 0 else Direction.UP
        # Horizontal movement dominates
        elif abs_h > abs_v and abs_h > h_threshold:
            return Direction.RIGHT if horizontal_velocity > 0 else Direction.LEFT
        else:
            return Direction.NONE
    
    def _calculate_articulation(
        self,
        acceleration: float,
        velocity: float
    ) -> float:
        """
        Calculate articulation score from acceleration and velocity.
        
        Higher acceleration relative to velocity = more abrupt = higher score
        
        Args:
            acceleration: Absolute acceleration value
            velocity: Absolute velocity value
            
        Returns:
            Articulation score between 0.0 and 1.0
        """
        if velocity < 0.01:
            return 0.0
        
        # Normalized ratio of acceleration to velocity
        # Adding small constant to prevent division issues
        ratio = acceleration / (velocity + 0.1)
        
        # Map to 0-1 range using sigmoid-like function
        # Higher threshold means more acceleration needed for high articulation
        normalized = ratio / self.acceleration_threshold
        articulation = np.tanh(normalized)
        
        return float(np.clip(articulation, 0.0, 1.0))
    
    def get_current_tempo(self, window: int = 4) -> Optional[float]:
        """
        Get current tempo based on recent beats.
        
        Args:
            window: Number of recent beats to consider
            
        Returns:
            Current tempo in BPM or None if insufficient data
        """
        if len(self.beat_history) < 2:
            return None
        
        # Use last N beats to calculate average tempo
        recent_beats = self.beat_history[-window:]
        
        if len(recent_beats) < 2:
            return None
        
        intervals = []
        for i in range(1, len(recent_beats)):
            interval = recent_beats[i].timestamp - recent_beats[i-1].timestamp
            if interval > 0:
                intervals.append(interval)
        
        if not intervals:
            return None
        
        # Calculate median interval (more robust than mean)
        median_interval = np.median(intervals)
        tempo_bpm = 60.0 / median_interval
        
        # Clamp to reasonable range
        tempo_bpm = np.clip(tempo_bpm, 30, 240)
        
        return float(tempo_bpm)
    
    def get_average_articulation(self, window: int = 4) -> float:
        """
        Get average articulation over recent beats.
        
        Args:
            window: Number of recent beats to consider
            
        Returns:
            Average articulation score (0.0 to 1.0)
        """
        if not self.beat_history:
            return 0.5
        
        recent_beats = self.beat_history[-window:]
        articulations = [beat.articulation for beat in recent_beats]
        
        return float(np.mean(articulations))
    
    def get_tempo_stability(self, window: int = 8) -> float:
        """
        Calculate tempo stability (consistency).
        
        Args:
            window: Number of recent beats to analyze
            
        Returns:
            Stability score (0.0 = unstable, 1.0 = very stable)
        """
        if len(self.beat_history) < 3:
            return 0.0
        
        recent_beats = self.beat_history[-window:]
        
        if len(recent_beats) < 3:
            return 0.0
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(recent_beats)):
            interval = recent_beats[i].timestamp - recent_beats[i-1].timestamp
            if interval > 0:
                intervals.append(interval)
        
        if len(intervals) < 2:
            return 0.0
        
        # Calculate coefficient of variation (CV)
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        if mean_interval == 0:
            return 0.0
        
        cv = std_interval / mean_interval
        
        # Map CV to stability score (lower CV = higher stability)
        # CV of 0.1 (10%) = stability of ~0.9
        # CV of 0.5 (50%) = stability of ~0.5
        stability = np.exp(-cv * 2)
        
        return float(np.clip(stability, 0.0, 1.0))
    
    def get_beat_strength(self, beat: BeatEvent) -> float:
        """
        Calculate the "strength" or emphasis of a beat.
        
        Args:
            beat: BeatEvent to analyze
            
        Returns:
            Strength score (0.0 to 1.0)
        """
        # Combine velocity and acceleration
        # Normalize assuming typical ranges
        velocity_component = min(1.0, beat.velocity / 5.0)
        acceleration_component = min(1.0, beat.acceleration / 10.0)
        
        # Weighted combination
        strength = 0.6 * velocity_component + 0.4 * acceleration_component
        
        return float(np.clip(strength, 0.0, 1.0))
    
    def detect_pattern(self, window: int = 8) -> Optional[str]:
        """
        Detect conducting pattern (e.g., 2/4, 3/4, 4/4).
        
        This is a simplified heuristic based on beat positions.
        
        Args:
            window: Number of recent beats to analyze
            
        Returns:
            Pattern string or None
        """
        if len(self.beat_history) < 4:
            return None
        
        recent_beats = self.beat_history[-window:]
        
        # Analyze y-position patterns
        y_positions = [beat.position[1] for beat in recent_beats]
        
        # Find local maxima and minima
        peaks, _ = find_peaks(y_positions, distance=1)
        valleys, _ = find_peaks([-y for y in y_positions], distance=1)
        
        # Estimate pattern based on peak/valley count
        cycle_length = len(peaks) + len(valleys)
        
        if cycle_length >= 6:
            return "4/4"  # Four beat pattern
        elif cycle_length >= 4:
            return "3/4"  # Three beat pattern
        elif cycle_length >= 2:
            return "2/4"  # Two beat pattern
        
        return None
    
    def clear_history(self, keep_recent: int = 0):
        """
        Clear beat history.
        
        Args:
            keep_recent: Number of recent beats to keep
        """
        if keep_recent > 0 and len(self.beat_history) > keep_recent:
            self.beat_history = self.beat_history[-keep_recent:]
        else:
            self.beat_history.clear()
            self.last_beat_time = None
        
        if self.beat_history:
            self.last_beat_time = self.beat_history[-1].timestamp
    
    def export_beats(self) -> List[dict]:
        """
        Export beat history as list of dictionaries.
        
        Returns:
            List of beat data dictionaries
        """
        return [
            {
                'timestamp': beat.timestamp,
                'position': beat.position,
                'velocity': beat.velocity,
                'acceleration': beat.acceleration,
                'direction': beat.direction.value,
                'tempo_bpm': beat.tempo_bpm,
                'articulation': beat.articulation
            }
            for beat in self.beat_history
        ]
    
    def get_statistics(self) -> dict:
        """
        Get comprehensive statistics about detected beats.
        
        Returns:
            Dictionary with statistical measures
        """
        if not self.beat_history:
            return {
                'total_beats': 0,
                'average_tempo': None,
                'tempo_std': None,
                'tempo_range': None,
                'average_articulation': None,
                'articulation_std': None,
                'average_velocity': None,
                'average_acceleration': None,
                'tempo_stability': 0.0,
                'direction_distribution': {},
                'total_duration': 0.0
            }
        
        # Extract metrics
        tempos = [b.tempo_bpm for b in self.beat_history if b.tempo_bpm is not None]
        articulations = [b.articulation for b in self.beat_history]
        velocities = [b.velocity for b in self.beat_history]
        accelerations = [b.acceleration for b in self.beat_history]
        directions = [b.direction.value for b in self.beat_history]
        
        # Calculate statistics
        stats = {
            'total_beats': len(self.beat_history),
            'average_tempo': float(np.mean(tempos)) if tempos else None,
            'tempo_std': float(np.std(tempos)) if tempos else None,
            'tempo_range': (float(np.min(tempos)), float(np.max(tempos))) if tempos else None,
            'average_articulation': float(np.mean(articulations)),
            'articulation_std': float(np.std(articulations)),
            'average_velocity': float(np.mean(velocities)),
            'average_acceleration': float(np.mean(accelerations)),
            'tempo_stability': self.get_tempo_stability(),
            'direction_distribution': self._get_direction_distribution(directions),
            'total_duration': self.beat_history[-1].timestamp - self.beat_history[0].timestamp
        }
        
        return stats
    
    def _get_direction_distribution(self, directions: List[str]) -> dict:
        """Calculate percentage distribution of directions."""
        from collections import Counter
        
        if not directions:
            return {}
        
        counts = Counter(directions)
        total = len(directions)
        
        return {
            direction: (count / total) * 100
            for direction, count in counts.items()
        }