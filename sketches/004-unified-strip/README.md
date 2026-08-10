## Variant: Unified strip

### Design stance
The whole journey on one surface: any constraint settable in any order, the list re-groups around what you've pinned.

### Key choices
- Layout: top bar (days / city / format / search) + pin-chips row + adaptive list + fixed seat pane
- Pinning: click a movie title → it becomes a chip, list regroups "By cinema"; city/cinema pins also removable
- Grouping adapts: nothing pinned → flat movie list w/ seat %; movie pinned → grouped by cinema; cinema pinned → grouped by movie
- Interaction: pin chips double as breadcrumbs (click × to unpin); seat % shown inline on every chip

### Trade-offs
- Strong at: every journey in one place, no mode toggle, minimal chrome
- Weak at: no day-axis view for a single movie (compare across days needs the grid toggle); the list can get long

### Best for
- The default daily driver — the surface that hosts all four journeys
