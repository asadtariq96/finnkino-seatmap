from pathlib import Path
import unittest


class StaticUiTests(unittest.TestCase):
    def test_ui_is_single_file_with_local_fonts_only(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        for marker in ['id="cinema"', 'id="days"', 'id="shows"', 'id="seatmap"', 'function loadSchedule', 'function loadSeatmap', 'function showFormat', 'class="format"', 'function autoSelect']:
            self.assertIn(marker, html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=", html)
        self.assertIn("@font-face", html)  # fonts bundled locally, not fetched

    def test_no_mode_toggle_unified_flow(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('data-mode="cinema"', html)
        self.assertNotIn('data-mode="movie"', html)
        self.assertIn('id="experience"', html)
        self.assertIn('id="city"', html)
        self.assertIn('value="All">All cities', html)
        self.assertIn('"All cinemas"', html)  # cinema scope label when all cities selected

    def test_desktop_seat_pane_is_fixed_right_column(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn(".main{min-height:0;display:grid;grid-template-columns:330px minmax(0,1fr)}", html)
        self.assertIn(".seatpane{min-width:0;min-height:0;border-left:1px solid var(--line);background:var(--panel);display:flex;flex-direction:column}", html)
        self.assertIn(".seatmap{flex:1;min-height:0;overflow:hidden;display:grid;place-items:center;padding:12px 16px 22px}", html)
        self.assertIn("function fitMap()", html)  # seat map scales to fit, never scrolls
        self.assertIn("requestAnimationFrame(fitMap)", html)

    def test_mobile_stacks_pane_below_list(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:1100px){.main{grid-template-columns:1fr;grid-template-rows:minmax(0,45%) minmax(0,55%)}", html)
        self.assertIn(".seatpane{border-left:0;border-top:1px solid var(--line)}", html)

    def test_rows_single_column_no_inner_scroll_desktop(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('grid-template-columns:repeat(auto-fit,minmax(320px,1fr))', html)
        self.assertIn(".shows{flex:1;min-height:0;overflow:auto;padding:6px 10px;", html)

    def test_auto_select_first_showtime_after_schedule_load(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("function autoSelect(groups)", html)
        self.assertIn("const groups=renderShows();autoSelect(groups)", html)  # called in loadSchedule
        self.assertIn("function pickShow(shows)", html)
        self.assertIn("setActivePref(start,siteId)", html)
        self.assertIn("resetSeatmap(\"Loading…\",true)", html)
        self.assertIn("loadSeatmap(pick.id,showTitle(pick),pick.schedule.startsAt,showFormat(pick),pick.siteId,false)", html)

    def test_chip_is_two_line_time_plus_format(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<span class="clock">', html)
        self.assertIn('<span class="format">', html)
        self.assertIn("show.isSoldOut?'sold':''", html)

    def test_seatmap_screen_and_legend_markup(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('${body}<div class="screen-bottom">', html)
        self.assertIn(".screen-bottom{margin-top:10px}", html)
        self.assertIn('class="legend"', html)

    def test_show_selection_keeps_rendering(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("state.active=id;", html)
        self.assertIn("setActivePref(start,siteId)", html)
        self.assertIn("if(rerender)renderShows()", html)
        self.assertNotIn("loadSeatmap(show.id", html)  # no implicit auto-load in render paths

    def test_search_filters_movies_and_fallback_autoselect(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('$("#search").oninput=', html)
        self.assertIn("if(!groups.some(g=>g.shows.some(s=>s.id===state.active)))autoSelect(groups)", html)

    def test_7day_grid_toggle_and_lazy_loading(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="gridToggle"', html)
        self.assertIn("function renderGridView()", html)
        self.assertIn("function loadMiniMap(card)", html)
        self.assertIn("new IntersectionObserver", html)  # lazy: only visible mini maps fetch seats
        self.assertIn("rootMargin:\"200px\"", html)
        self.assertIn("function openFromGrid(card)", html)
        self.assertIn("function fitMiniMap(card,data)", html)
        self.assertIn(".mm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;align-items:start}", html)
        self.assertIn("class=\"minimap", html)
        self.assertIn("7-day grid", html)

    def test_grid_respects_filters_and_days(self):
        html = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("function gridShows(payload)", html)
        self.assertIn("matchesExperience(x.show,x.attrs)&&matchesSite(x.show)", html)
        self.assertIn("(!state.selectedFilm||x.show.filmId===state.selectedFilm)", html)
        self.assertIn("function matchesSite(show)", html)
        self.assertIn("function persistFilm(id)", html)
        self.assertIn("Array.from({length:7},(_,i)=>dayISO(i))", html)  # all 7 days fetched
        self.assertIn("Promise.all(dates.map(d=>fetchSchedule(d)))", html)  # cached 7-day fetch
        self.assertIn('if(document.querySelector("#gridToggle").classList.contains("on"))renderGridView();else loadSchedule()', html)


if __name__ == "__main__":
    unittest.main()
