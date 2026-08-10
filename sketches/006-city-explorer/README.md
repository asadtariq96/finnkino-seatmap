## Variant: City explorer

### Design stance
The place-first journey: city tabs on top, each city's cinemas as expandable cards, summary stats up front.

### Key choices
- Layout: city tabs (Helsinki/Tampere/Turku/All) + day tabs + summary stat row + cinema cards + seat pane
- Cards: cinema name, film/show counts; expand to reveal movies with seat-% showtime chips
- Interaction: click card header to expand/collapse; city or format change collapses all; one click on a chip → seats
- Summary row: "4 cinemas · 35 shows today · 10 films" — instant city context

### Trade-offs
- Strong at: "what's on in my city today" browsing; clear location-first mental model
- Weak at: comparing a single movie across cities (no movie focus); expanded cards get long

### Best for
- The place-first journey — deciding to go to the cinema, then picking a film
