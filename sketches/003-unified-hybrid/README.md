## Variant: Unified hybrid

### Design stance
No modes, no hidden panels. One continuous flow: every movie with its showtimes grouped by cinema on the left, the seat panel permanently reserved on the right. The Cinema/Movie toggle is dead.

### Key choices
- Layout: fluid list (movies × cinemas × chips) + fixed 430px seat pane, always visible
- Typography: system sans; chips are two-line (time + format), cinema names as group headers
- Color: auditorium ink + amber accent + steel-blue screen glow
- Interaction: one click on any chip → seats in the right pane; All/One cinema segmented control replaces the old mode toggle

### Trade-offs
- Strong at: comparing a movie across cinemas in one scroll; seat panel never moves (zero layout shift); simplest mental model
- Weak at: no time-axis view; list gets long with many movies (mitigated by search/format filter)

### Best for
- The main daily flow: pick a movie, see where it plays, click the best time, read the seats
