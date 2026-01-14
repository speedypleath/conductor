<<
  \new Voice { 
    \clef bass 
    \time 4/4
    \key c \major
    % 16-bar figured bass progression with varied harmony
    % Bars 1-4: Opening progression
    c4 c f f | g g c c | a, a, d d | g g g, g, |
    % Bars 5-8: Modulation and development
    c c e e | a, a, d d | g g f f | e e e e |
    % Bars 9-12: Secondary dominants
    a, a, d d | g g c c | f f b, b, | e e a, a, |
    % Bars 13-16: Final cadence
    d d g, g, | c c f f | g g g, g, | c c c2
  }
  \new FiguredBass {
    \figuremode {
      % Bars 1-4
      <_>4 <_> <_> <6> | <7> <6> <_> <_> | <6> <_> <6> <_> | <7> <6 4> <_> <_> |
      % Bars 5-8
      <_>4 <_> <6> <_> | <6> <_> <6> <7> | <7> <6> <6> <_> | <6> <6 5> <_> <_> |
      % Bars 9-12
      <6>4 <7> <6> <_> | <7> <6> <_> <6> | <_> <6> <6> <7> | <6> <_> <6> <7> |
      % Bars 13-16
      <6>4 <_> <7> <6> | <_> <_> <_> <6> | <7> <6 4> <_> <_> | <_> <_> <_>2
    }
  }
>>
