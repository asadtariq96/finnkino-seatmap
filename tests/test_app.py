import json
import os
import unittest
from unittest.mock import patch
from app import extract_api_config, pick_showtimes, build_seat_map, window_dates, multi_site_schedule_path, Finnkino, load_token_config, token_expires_in
from datetime import date


class FinnkinoCoreTests(unittest.TestCase):
    def test_extracts_api_configuration_from_rendered_html(self):
        html = r'<script>{\"api\":{\"apiUrl\":\"https://api.example.test/root\",\"authToken\":\"abc.def.ghi\"}}</script>'
        config = extract_api_config(html)
        self.assertEqual(config["api_url"], "https://api.example.test/root")
        self.assertEqual(config["token"], "abc.def.ghi")

    def test_filters_showtimes_by_movie_and_orders_by_start_time(self):
        payload = {
            "showtimes": [
                {"id": "late", "filmId": "movie-a", "schedule": {"startsAt": "2026-08-01T20:00:00+03:00"}},
                {"id": "other", "filmId": "movie-b", "schedule": {"startsAt": "2026-08-01T10:00:00+03:00"}},
                {"id": "early", "filmId": "movie-a", "schedule": {"startsAt": "2026-08-01T12:00:00+03:00"}},
            ]
        }
        self.assertEqual([s["id"] for s in pick_showtimes(payload, "movie-a")], ["early", "late"])

    def test_joins_layout_labels_with_live_availability(self):
        layout = {"seatLayout": {"areas": [{"name": {"text": "Standard"}, "rows": [{"label": "10", "seats": [
            {"id": "1_1_5", "label": "15", "type": "Normal", "position": {"rowNumber": 1, "columnNumber": 5}},
            {"id": "1_1_6", "label": "14", "type": "Normal", "position": {"rowNumber": 1, "columnNumber": 6}},
        ]}]}]}}
        availability = {"seatAvailabilities": [{"seatId": "1_1_5", "status": "Sold"}, {"seatId": "1_1_6", "status": "Available"}]}
        result = build_seat_map(layout, availability)
        self.assertEqual(result["counts"], {"total": 2, "available": 1, "unavailable": 1})
        self.assertEqual(result["areas"][0]["rows"][0]["seats"][0]["status"], "Sold")
        self.assertEqual(result["areas"][0]["rows"][0]["seats"][1]["label"], "14")

    def test_builds_today_plus_six_day_window(self):
        self.assertEqual(
            window_dates(date(2026, 7, 29)),
            ["2026-07-29", "2026-07-30", "2026-07-31", "2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"],
        )

    def test_default_window_works_without_system_timezone_database(self):
        dates = window_dates()
        self.assertEqual(len(dates), 7)
        self.assertEqual(len(set(dates)), 7)

    def test_builds_multi_site_schedule_path_for_movie_view(self):
        self.assertEqual(
            multi_site_schedule_path("2026-07-29", ["1100", "1004"]),
            "showtimes/by-business-date/2026-07-29?siteIds=1100&siteIds=1004",
        )

    def test_backfills_combined_schedule_into_each_site_cache(self):
        client = Finnkino()
        payload = {
            "businessDate": "2026-07-29",
            "showtimes": [
                {"id": "a", "siteId": "1100", "seatLayoutId": "layout-a"},
                {"id": "b", "siteId": "1004", "seatLayoutId": "layout-b"},
            ],
            "relatedData": {"films": [{"id": "film-a"}]},
        }
        client.backfill_schedule("2026-07-29", ["1100", "1004"], payload)
        one, _ = client.cache.get("showtimes/by-business-date/2026-07-29?siteIds=1100")
        two, _ = client.cache.get("showtimes/by-business-date/2026-07-29?siteIds=1004")
        self.assertEqual([show["id"] for show in one["showtimes"]], ["a"])
        self.assertEqual([show["id"] for show in two["showtimes"]], ["b"])
        self.assertEqual(client.show_index["a"], "layout-a")

    def test_load_token_config_from_env(self):
        with patch.dict(os.environ, {"FINNKINO_TOKEN": "test.jwt.token"}, clear=False):
            self.assertEqual(load_token_config(), {"token": "test.jwt.token"})

    def test_token_expires_in_reads_jwt_exp(self):
        import base64
        payload = base64.urlsafe_b64encode(json.dumps({"exp": 2000000000}).encode()).decode().rstrip("=")
        token = f"hdr.{payload}.sig"
        remaining = token_expires_in(token)
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)


if __name__ == "__main__":
    unittest.main()
