"""
Figured bass realization module for generating musical accompaniment.
Converts figured bass notation into complete chord voicings following
common practice harmony rules.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class VoiceType(Enum):
    """Voice types for SATB realization."""
    SOPRANO = "soprano"
    ALTO = "alto"
    TENOR = "tenor"
    BASS = "bass"


@dataclass
class VoiceRange:
    """Pitch range for a voice type."""
    lowest: int  # MIDI note number
    highest: int
    
    def contains(self, pitch: int) -> bool:
        """Check if pitch is in range."""
        return self.lowest <= pitch <= self.highest


# Standard SATB voice ranges
VOICE_RANGES = {
    VoiceType.SOPRANO: VoiceRange(60, 81),  # C4 to A5
    VoiceType.ALTO: VoiceRange(55, 74),     # G3 to D5
    VoiceType.TENOR: VoiceRange(48, 69),    # C3 to A4
    VoiceType.BASS: VoiceRange(40, 64)      # E2 to E4
}


@dataclass
class FiguredBassSymbol:
    """
    Represents a figured bass symbol.
    
    Examples:
        6 = first inversion triad
        6/4 = second inversion triad
        7 = seventh chord in root position
        6/5 = first inversion seventh chord
        4/3 = second inversion seventh chord
        4/2 = third inversion seventh chord
    """
    bass_note: int  # MIDI note number
    figures: List[int]  # Interval numbers above bass
    accidentals: Dict[int, int]  # figure -> accidental (-1, 0, +1)
    duration: float = 1.0  # Duration in beats
    
    @classmethod
    def from_string(cls, bass_note: int, figure_str: str, duration: float = 1.0):
        """
        Create from string notation.
        
        Args:
            bass_note: MIDI note number for bass
            figure_str: Figure notation (e.g., "6", "6/4", "7", "6/5")
            duration: Duration in beats
            
        Returns:
            FiguredBassSymbol instance
        """
        figures = []
        accidentals = {}
        
        if not figure_str or figure_str == "" or figure_str == "5/3":
            # Root position triad (default)
            figures = [3, 5]
        elif figure_str == "6" or figure_str == "6/3":
            # First inversion triad
            figures = [3, 6]
        elif figure_str == "6/4":
            # Second inversion triad
            figures = [4, 6]
        elif figure_str == "7" or figure_str == "7/5/3":
            # Root position seventh chord
            figures = [3, 5, 7]
        elif figure_str == "6/5" or figure_str == "6/5/3":
            # First inversion seventh chord
            figures = [3, 5, 6]
        elif figure_str == "4/3" or figure_str == "6/4/3":
            # Second inversion seventh chord
            figures = [3, 4, 6]
        elif figure_str == "4/2" or figure_str == "6/4/2":
            # Third inversion seventh chord
            figures = [2, 4, 6]
        elif figure_str == "9":
            # Ninth chord
            figures = [3, 5, 7, 9]
        else:
            # Parse custom figures
            parts = figure_str.split('/')
            for part in parts:
                # Handle accidentals
                accidental = 0
                if '#' in part:
                    accidental = 1
                    part = part.replace('#', '')
                elif 'b' in part:
                    accidental = -1
                    part = part.replace('b', '')
                
                if part.isdigit():
                    figure = int(part)
                    figures.append(figure)
                    if accidental != 0:
                        accidentals[figure] = accidental
        
        return cls(
            bass_note=bass_note,
            figures=sorted(figures),
            accidentals=accidentals,
            duration=duration
        )


@dataclass
class Chord:
    """Represents a realized chord with specific voicings."""
    bass: int
    tenor: int
    alto: int
    soprano: int
    duration: float = 1.0
    
    def get_notes(self) -> List[int]:
        """Get all notes in the chord."""
        return [self.bass, self.tenor, self.alto, self.soprano]
    
    def get_intervals(self) -> List[int]:
        """Get intervals between adjacent voices."""
        notes = self.get_notes()
        return [notes[i+1] - notes[i] for i in range(len(notes)-1)]
    
    def has_parallel_fifths(self, other: 'Chord') -> bool:
        """Check for parallel perfect fifths with another chord."""
        return self._has_parallel_interval(other, 7)
    
    def has_parallel_octaves(self, other: 'Chord') -> bool:
        """Check for parallel octaves with another chord."""
        return self._has_parallel_interval(other, 12)
    
    def _has_parallel_interval(self, other: 'Chord', interval: int) -> bool:
        """Check for parallel intervals between voices."""
        voices1 = self.get_notes()
        voices2 = other.get_notes()
        
        for i in range(len(voices1)):
            for j in range(i + 1, len(voices1)):
                interval1 = (voices1[j] - voices1[i]) % 12
                interval2 = (voices2[j] - voices2[i]) % 12
                
                if interval1 == interval % 12 and interval2 == interval % 12:
                    # Check if motion is parallel
                    motion1 = voices1[j] - voices1[i]
                    motion2 = voices2[j] - voices2[i]
                    if (motion2 - motion1) == (voices2[i] - voices1[i]):
                        return True
        
        return False


class FiguredBassRealizer:
    """Main class for figured bass realization."""
    
    def __init__(
        self,
        key: str = "C",
        mode: str = "major",
        voice_ranges: Optional[Dict[VoiceType, VoiceRange]] = None
    ):
        """
        Initialize realizer.
        
        Args:
            key: Key signature (e.g., "C", "G", "Bb")
            mode: Mode ("major" or "minor")
            voice_ranges: Optional custom voice ranges
        """
        self.key = key
        self.mode = mode
        self.voice_ranges = voice_ranges or VOICE_RANGES
        self.scale = self._build_scale()
        
    def _build_scale(self) -> List[int]:
        """Build scale based on key and mode."""
        # Note name to MIDI number (C4 = 60)
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Find root
        root = note_names.index(self.key.replace('b', '♭').replace('#', '♯'))
        
        # Scale intervals
        if self.mode == "major":
            intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
        
        return [(root + interval) % 12 for interval in intervals]
    
    def realize_figured_bass(
        self,
        figured_bass: List[FiguredBassSymbol],
        style: str = "strict"
    ) -> List[Chord]:
        """
        Realize a sequence of figured bass symbols.
        
        Args:
            figured_bass: List of figured bass symbols
            style: Realization style ("strict", "free", "keyboard")
            
        Returns:
            List of realized chords
        """
        chords = []
        previous_chord = None
        
        for symbol in figured_bass:
            # Generate possible voicings
            candidates = self._generate_voicings(symbol)
            
            if not candidates:
                # If no valid voicings, use simple octave doubling
                candidates = [self._simple_voicing(symbol)]
            
            # Select best voicing
            if previous_chord is None:
                # First chord: prefer root position with soprano on root or fifth
                chord = self._select_opening_voicing(candidates)
            else:
                # Select based on voice leading
                chord = self._select_best_voicing(
                    candidates,
                    previous_chord,
                    style
                )
            
            chord.duration = symbol.duration
            chords.append(chord)
            previous_chord = chord
        
        return chords
    
    def _generate_voicings(
        self,
        symbol: FiguredBassSymbol
    ) -> List[Chord]:
        """
        Generate all possible valid voicings for a figured bass symbol.
        
        Args:
            symbol: Figured bass symbol to realize
            
        Returns:
            List of possible chord voicings
        """
        voicings = []
        
        # Calculate chord tones from figures
        chord_tones = self._calculate_chord_tones(symbol)
        
        # Generate all combinations of notes within voice ranges
        bass_note = symbol.bass_note
        
        # Tenor range (above bass)
        tenor_candidates = [
            n for n in chord_tones
            if self.voice_ranges[VoiceType.TENOR].contains(n) and n > bass_note
        ]
        
        for tenor in tenor_candidates:
            # Alto range (above tenor)
            alto_candidates = [
                n for n in chord_tones
                if self.voice_ranges[VoiceType.ALTO].contains(n) and n >= tenor
            ]
            
            for alto in alto_candidates:
                # Soprano range (above alto)
                soprano_candidates = [
                    n for n in chord_tones
                    if self.voice_ranges[VoiceType.SOPRANO].contains(n) and n >= alto
                ]
                
                for soprano in soprano_candidates:
                    # Check if voicing is valid
                    chord = Chord(bass_note, tenor, alto, soprano)
                    if self._is_valid_voicing(chord, symbol):
                        voicings.append(chord)
        
        return voicings
    
    def _calculate_chord_tones(
        self,
        symbol: FiguredBassSymbol
    ) -> List[int]:
        """
        Calculate actual pitches from figured bass symbol.
        
        Args:
            symbol: Figured bass symbol
            
        Returns:
            List of MIDI note numbers for chord tones
        """
        chord_tones = [symbol.bass_note]
        
        for figure in symbol.figures:
            # Calculate interval from bass
            # Figure numbers represent diatonic intervals
            interval_semitones = self._figure_to_semitones(figure)
            
            # Apply accidentals
            if figure in symbol.accidentals:
                interval_semitones += symbol.accidentals[figure]
            
            # Add notes in multiple octaves for flexibility
            for octave in range(-1, 3):
                note = symbol.bass_note + interval_semitones + (octave * 12)
                if 40 <= note <= 84:  # Reasonable MIDI range
                    chord_tones.append(note)
        
        return sorted(list(set(chord_tones)))
    
    def _figure_to_semitones(self, figure: int) -> int:
        """
        Convert figured bass interval number to semitones.
        
        Args:
            figure: Interval number (e.g., 3, 5, 7)
            
        Returns:
            Number of semitones
        """
        # Diatonic intervals in major scale
        intervals = {
            1: 0,   # Unison
            2: 2,   # Major second
            3: 4,   # Major third
            4: 5,   # Perfect fourth
            5: 7,   # Perfect fifth
            6: 9,   # Major sixth
            7: 11,  # Major seventh
            8: 12,  # Octave
            9: 14,  # Major ninth
            10: 16, # Major tenth
            11: 17, # Perfect eleventh
            13: 21  # Major thirteenth
        }
        
        # Adjust for minor mode if needed
        if self.mode == "minor" and figure == 3:
            return 3  # Minor third
        
        return intervals.get(figure, 0)
    
    def _is_valid_voicing(self, chord: Chord, symbol: FiguredBassSymbol) -> bool:
        """
        Check if a voicing follows common practice rules.
        
        Args:
            chord: Chord voicing to check
            symbol: Original figured bass symbol
            
        Returns:
            True if voicing is valid
        """
        # Check voice ranges
        if not self.voice_ranges[VoiceType.BASS].contains(chord.bass):
            return False
        if not self.voice_ranges[VoiceType.TENOR].contains(chord.tenor):
            return False
        if not self.voice_ranges[VoiceType.ALTO].contains(chord.alto):
            return False
        if not self.voice_ranges[VoiceType.SOPRANO].contains(chord.soprano):
            return False
        
        # Check spacing between upper voices (should be less than octave)
        if chord.alto - chord.tenor > 12:
            return False
        if chord.soprano - chord.alto > 12:
            return False
        
        # Check that all chord tones are present
        chord_pcs = set((n % 12) for n in chord.get_notes())
        required_pcs = set((symbol.bass_note + self._figure_to_semitones(f)) % 12 
                          for f in symbol.figures)
        required_pcs.add(symbol.bass_note % 12)
        
        # At least 3 different pitch classes for triads
        if len(chord_pcs) < 3:
            return False
        
        return True
    
    def _simple_voicing(self, symbol: FiguredBassSymbol) -> Chord:
        """
        Create simple voicing when no complex options available.
        
        Args:
            symbol: Figured bass symbol
            
        Returns:
            Simple chord voicing
        """
        bass = symbol.bass_note
        tenor = bass + 12  # Octave above
        alto = bass + 19   # Fifth + octave
        soprano = bass + 24  # Two octaves above
        
        return Chord(bass, tenor, alto, soprano)
    
    def _select_opening_voicing(self, candidates: List[Chord]) -> Chord:
        """
        Select best voicing for opening chord.
        
        Args:
            candidates: List of possible voicings
            
        Returns:
            Selected chord
        """
        # Prefer complete chords with soprano on root or fifth
        def score_opening(chord: Chord) -> float:
            score = 0.0
            
            # Prefer soprano on root (highest priority)
            if (chord.soprano % 12) == (chord.bass % 12):
                score += 10.0
            # Or fifth
            elif (chord.soprano - chord.bass) % 12 == 7:
                score += 5.0
            
            # Prefer wider spacing
            score += sum(chord.get_intervals()) * 0.1
            
            # Penalize extreme ranges
            if chord.soprano > 76:  # Above E5
                score -= 2.0
            
            return score
        
        return max(candidates, key=score_opening)
    
    def _select_best_voicing(
        self,
        candidates: List[Chord],
        previous: Chord,
        style: str
    ) -> Chord:
        """
        Select best voicing based on voice leading.
        
        Args:
            candidates: Possible voicings
            previous: Previous chord
            style: Realization style
            
        Returns:
            Best voicing
        """
        def score_voicing(chord: Chord) -> float:
            score = 0.0
            
            # Calculate total voice leading distance
            distances = [
                abs(chord.soprano - previous.soprano),
                abs(chord.alto - previous.alto),
                abs(chord.tenor - previous.tenor),
                abs(chord.bass - previous.bass)
            ]
            
            # Prefer minimal motion (most important)
            score -= sum(distances) * 2.0
            
            # Prefer contrary motion
            bass_motion = chord.bass - previous.bass
            soprano_motion = chord.soprano - previous.soprano
            if bass_motion * soprano_motion < 0:  # Opposite directions
                score += 5.0
            
            # Penalize parallel fifths and octaves (strict style)
            if style == "strict":
                if chord.has_parallel_fifths(previous):
                    score -= 100.0
                if chord.has_parallel_octaves(previous):
                    score -= 100.0
            
            # Penalize voice crossing
            prev_notes = previous.get_notes()
            curr_notes = chord.get_notes()
            for i in range(len(curr_notes)):
                for j in range(i + 1, len(curr_notes)):
                    if (prev_notes[i] < prev_notes[j]) != (curr_notes[i] < curr_notes[j]):
                        score -= 5.0
            
            # Prefer common tones
            common_pcs = set((n % 12) for n in previous.get_notes()) & \
                        set((n % 12) for n in chord.get_notes())
            score += len(common_pcs) * 2.0
            
            return score
        
        return max(candidates, key=score_voicing)
    
    def chord_to_midi_notes(self, chord: Chord) -> List[Tuple[int, float]]:
        """
        Convert chord to MIDI note list.
        
        Args:
            chord: Chord to convert
            
        Returns:
            List of (note, duration) tuples
        """
        return [
            (chord.bass, chord.duration),
            (chord.tenor, chord.duration),
            (chord.alto, chord.duration),
            (chord.soprano, chord.duration)
        ]


# Example usage functions
def realize_simple_progression():
    """Example: Realize a simple I-IV-V-I progression."""
    realizer = FiguredBassRealizer(key="C", mode="major")
    
    # C major: C - F - G - C (bass notes)
    figured_bass = [
        FiguredBassSymbol.from_string(48, "", 1.0),      # I (C)
        FiguredBassSymbol.from_string(53, "", 1.0),      # IV (F)
        FiguredBassSymbol.from_string(55, "7", 1.0),     # V7 (G7)
        FiguredBassSymbol.from_string(48, "", 1.0),      # I (C)
    ]
    
    chords = realizer.realize_figured_bass(figured_bass, style="strict")
    
    for i, chord in enumerate(chords):
        print(f"Chord {i+1}: Bass={chord.bass}, Tenor={chord.tenor}, "
              f"Alto={chord.alto}, Soprano={chord.soprano}")
    
    return chords


def realize_bach_chorale_style():
    """Example: Realize figured bass in Bach chorale style."""
    realizer = FiguredBassRealizer(key="G", mode="major")
    
    # More complex progression with inversions
    figured_bass = [
        FiguredBassSymbol.from_string(55, "", 1.0),      # I
        FiguredBassSymbol.from_string(59, "6", 1.0),     # I6
        FiguredBassSymbol.from_string(62, "6/4", 0.5),   # V6/4
        FiguredBassSymbol.from_string(62, "7", 0.5),     # V7
        FiguredBassSymbol.from_string(55, "", 1.0),      # I
    ]
    
    return realizer.realize_figured_bass(figured_bass, style="strict")


if __name__ == "__main__":
    print("Realizing simple progression:")
    chords = realize_simple_progression()
    
    print("\nRealizing Bach chorale style:")
    bach_chords = realize_bach_chorale_style()
