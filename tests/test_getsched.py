from unittest.mock import patch
from datetime import datetime
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from w2w_getsched import dtoConv, getSchedule, getNextGame, getPreviousGame


SAMPLE_HTML = (
    "<html><body><table>"
    "<tr><th>Day/Time</th><th>Field</th><th>Home</th><th>Visitor</th><th>Result</th></tr>"
    "<tr><td>Mon 01/13 10:00 AM</td><td>Field 1</td><td>Team A</td><td>Team B</td><td>2-1</td></tr>"
    "<tr><td>Mon 01/20 10:00 AM</td><td>Field 2</td><td>Team C</td><td>Team A</td><td></td></tr>"
    "<tr><td>Mon 01/27 10:00 AM</td><td>Field 1</td><td>Team A</td><td>Team D</td><td></td></tr>"
    "</table></body></html>"
)

MOCK_SCHEDULE = [
    ["Mon 01/13 10:00 AM", "Field 1", "Team A", "Team B", "2-1"],
    ["Mon 01/20 10:00 AM", "Field 2", "Team C", "Team A", "1-0"],
    ["Mon 01/27 10:00 AM", "Field 1", "Team A", "Team D", ""],
]


class TestDtoConv:
    def test_basic_parsing(self):
        result = dtoConv("03/15 10:00 AM")
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 0

    def test_year_rollover(self):
        with patch("w2w_getsched.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 12, 15)
            mock_dt.strptime.side_effect = datetime.strptime
            result = dtoConv("01/15 10:00 AM")
            assert result.year == 2026

    def test_no_year_rollover_mid_year(self):
        with patch("w2w_getsched.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15)
            mock_dt.strptime.side_effect = datetime.strptime
            result = dtoConv("08/15 10:00 AM")
            assert result.year == 2025

    def test_no_rollover_when_not_december(self):
        with patch("w2w_getsched.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 11, 15)
            mock_dt.strptime.side_effect = datetime.strptime
            result = dtoConv("01/15 10:00 AM")
            assert result.year == 2025


class TestGetSchedule:
    def test_returns_data_rows(self):
        with patch("w2w_getsched.getTeamData", return_value=SAMPLE_HTML):
            rows = list(getSchedule("Team A", 123))
            assert len(rows) == 3

    def test_skips_header_row(self):
        with patch("w2w_getsched.getTeamData", return_value=SAMPLE_HTML):
            rows = list(getSchedule("Team A", 123))
            for row in rows:
                assert "Day/Time" not in row

    def test_row_contents(self):
        with patch("w2w_getsched.getTeamData", return_value=SAMPLE_HTML):
            rows = list(getSchedule("Team A", 123))
            assert rows[0][0] == "Mon 01/13 10:00 AM"
            assert rows[0][1] == "Field 1"
            assert rows[0][2] == "Team A"
            assert rows[0][3] == "Team B"
            assert rows[0][4] == "2-1"

    def test_empty_schedule(self):
        empty_html = "<html><body><table><tr><th>Day/Time</th></tr></table></body></html>"
        with patch("w2w_getsched.getTeamData", return_value=empty_html):
            rows = list(getSchedule("Team A", 123))
            assert len(rows) == 0


class TestGetNextGame:
    def test_finds_next_game_after_date(self):
        ftime = datetime(2026, 1, 14, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getNextGame("Team A", 123, ftime=ftime)
            assert result[0] == "Mon 01/20 10:00 AM"

    def test_returns_first_upcoming(self):
        ftime = datetime(2026, 1, 12, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getNextGame("Team A", 123, ftime=ftime)
            assert result[0] == "Mon 01/13 10:00 AM"

    def test_no_future_games_returns_none(self):
        ftime = datetime(2026, 1, 28, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getNextGame("Team A", 123, ftime=ftime)
            assert result is None

    def test_uses_current_time_by_default(self):
        fake_now = datetime(2026, 1, 19, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            with patch("w2w_getsched.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.strptime.side_effect = datetime.strptime
                result = getNextGame("Team A", 123)
                assert result[0] == "Mon 01/20 10:00 AM"


class TestGetPreviousGame:
    def test_finds_most_recent_past_game(self):
        ftime = datetime(2026, 1, 21, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getPreviousGame("Team A", 123, ftime=ftime)
            assert result[0] == "Mon 01/20 10:00 AM"

    def test_no_past_games_returns_none(self):
        ftime = datetime(2026, 1, 12, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getPreviousGame("Team A", 123, ftime=ftime)
            assert result is None

    def test_returns_last_game_after_all_played(self):
        ftime = datetime(2026, 1, 28, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            result = getPreviousGame("Team A", 123, ftime=ftime)
            assert result[0] == "Mon 01/27 10:00 AM"

    def test_uses_current_time_by_default(self):
        fake_now = datetime(2026, 1, 21, 0, 0)
        with patch("w2w_getsched.getSchedule", return_value=iter(MOCK_SCHEDULE)):
            with patch("w2w_getsched.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.strptime.side_effect = datetime.strptime
                result = getPreviousGame("Team A", 123)
                assert result[0] == "Mon 01/20 10:00 AM"
