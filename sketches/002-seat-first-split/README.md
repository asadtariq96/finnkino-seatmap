## Variant: Seat-first split

### Design stance
The auditorium is the product. The seat map owns the stage; the movie rail is just a launcher. Zero clicks: first show is pre-selected, seats render on load.

### Key choices
- Layout: 250px movie rail + full-height seat stage; big 13px seats, row labels, wide screen arc
- Typography: system sans; bold titles in rail, quiet metadata
- Color: auditorium ink + amber accent + steel-blue screen glow
- Interaction: click a time chip → stage updates; click a movie row → first showtime loads; chips inline under each title

### Trade-offs
- Strong at: seat-centric workflow (compare occupancy across showtimes fast), big readable seat map, minimal chrome
- Weak at: whole-day planning (no time axis), many movies → long rail scroll

### Best for
- Someone who cares most about *where* they sit and wants the biggest possible seat map
