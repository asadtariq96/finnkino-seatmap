## Variant: Timetable matrix

### Design stance
The schedule is the interface: movies as rows, hours as columns — you read the whole day's shape at a glance and click one cell to see seats.

### Key choices
- Layout: sticky-header matrix (movie × hour), 12 hour columns; seat dock slides in as a right column
- Typography: system sans, tabular numerals for times
- Color: auditorium ink + amber accent + steel-blue screen glow
- Interaction: one click on any cell → dock opens with seat map; search + format + cinema filter the matrix

### Trade-offs
- Strong at: spotting patterns (which hours are busy, which movies have evening shows), max density, zero navigation
- Weak at: showing "which cinemas" per show (it's a one-cinema view), minute-granularity (cells are hour buckets)

### Best for
- A power user who plans a whole day/week of screenings and wants availability in one sweep
