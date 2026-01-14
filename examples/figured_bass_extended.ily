<<
  \new Voice { 
    \clef bass 
    \time 4/4
    \key c \major
    % I - IV - V7 - I progression in C major (8 bars)
    c4 c g, g, | c c f f | g g g, g, | c c c c |
    % ii - V - I - vi progression (4 bars)
    d d g, g, | c c a, a, |
    % IV - V7 - I with passing tones (4 bars)
    f f g g | c c c c |
    % Circle of fifths: vi - ii - V - I (4 bars)
    a, a, d d | g g c c |
    % Deceptive cadence and final resolution (4 bars)
    g g a, a, | d d g, g, | c c c c | c c c2
  }
  \new FiguredBass {
    \figuremode {
      % Bar 1-2: I - IV - V7 - I
      <_>4 <_> <_> <_> | <_> <_> <_> <6> |
      % Bar 3-4: V7 - I
      <7>4 <6> <7> <6> | <_> <_> <_> <_> |
      % Bar 5-6: ii - V - I - vi
      <6>4 <_> <7> <6> | <_> <_> <6>4 <_> |
      % Bar 7-8: IV - V7 - I
      <_>4 <6> <7> <6 4> | <_> <_> <_> <_> |
      % Bar 9-10: vi - ii - V - I
      <6>4 <_> <6> <_> | <7> <6> <_> <_> |
      % Bar 11-12: Deceptive cadence
      <7>4 <6> <6> <_> | <6> <_> <7> <6> |
      % Bar 13-14: Final resolution
      <_>4 <_> <_> <_> | <_> <_> <_>2
    }
  }
>>
