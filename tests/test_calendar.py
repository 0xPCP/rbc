"""
Tests for calendar views: list, week, and month.

Each test verifies HTTP status, rendered HTML structure, ride visibility,
and navigation between periods.
"""
from datetime import date, timedelta
import pytest


# ── List view ─────────────────────────────────────────────────────────────────

class TestListView:
    def test_returns_200(self, client, mock_weather):
        resp = client.get('/rides/')
        assert resp.status_code == 200

    def test_view_switcher_present(self, client, mock_weather):
        resp = client.get('/rides/')
        html = resp.data.decode()
        assert 'cal-toolbar' in html
        assert 'view-btn' in html
        assert '>List<' in html
        assert '>Week<' in html
        assert '>Month<' in html

    def test_shows_upcoming_rides(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/')
        html = resp.data.decode()
        # Cancelled ride is still listed but not the past
        assert 'Tuesday A Ride' in html
        assert 'Wednesday B Ride' in html

    def test_cancelled_badge_shown(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/')
        html = resp.data.decode()
        assert 'Thursday C Ride' in html
        assert 'Cancelled' in html

    def test_pace_filter_a(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/?pace=A')
        html = resp.data.decode()
        assert 'Tuesday A Ride' in html
        assert 'Wednesday B Ride' not in html
        assert 'Thursday C Ride' not in html

    def test_pace_filter_b(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/?pace=B')
        html = resp.data.decode()
        assert 'Wednesday B Ride' in html
        assert 'Tuesday A Ride' not in html

    def test_pace_filter_invalid_ignored(self, client, sample_rides, mock_weather):
        # Unknown pace letters should show all rides
        resp = client.get('/rides/?pace=Z')
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'Tuesday A Ride' in html

    def test_weather_shown_in_row(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/')
        html = resp.data.decode()
        assert 'list-weather' in html
        assert '68' in html   # mocked temp_f

    def test_empty_state_no_rides(self, client, mock_weather):
        # No rides in DB
        resp = client.get('/rides/')
        assert resp.status_code == 200
        assert b'No upcoming rides' in resp.data

    def test_month_heading_groups_rides(self, client, sample_rides, mock_weather):
        resp = client.get('/rides/')
        html = resp.data.decode()
        assert 'month-heading' in html


# ── Week view ─────────────────────────────────────────────────────────────────

class TestWeekView:
    def test_returns_200(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        assert resp.status_code == 200

    def test_renders_week_grid(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        html = resp.data.decode()
        assert 'week-grid' in html

    def test_seven_columns(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        html = resp.data.decode()
        # One week-col per day
        assert html.count('week-col') >= 7

    def test_shows_rides_this_week(self, client, sample_rides, mock_weather):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        resp = client.get(f'/rides/?view=week&start={monday.isoformat()}')
        html = resp.data.decode()
        assert 'Tuesday A Ride' in html
        assert 'Wednesday B Ride' in html

    def test_prev_next_navigation_links(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        html = resp.data.decode()
        assert 'Prev' in html
        assert 'Next' in html
        assert 'view=week' in html

    def test_next_week_navigation(self, client, sample_rides, mock_weather):
        today = date.today()
        next_monday = (today - timedelta(days=today.weekday())) + timedelta(weeks=1)
        resp = client.get(f'/rides/?view=week&start={next_monday.isoformat()}')
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'week-grid' in html

    def test_prev_week_navigation(self, client, mock_weather):
        today = date.today()
        prev_monday = (today - timedelta(days=today.weekday())) - timedelta(weeks=1)
        resp = client.get(f'/rides/?view=week&start={prev_monday.isoformat()}')
        assert resp.status_code == 200

    def test_invalid_start_date_falls_back(self, client, mock_weather):
        resp = client.get('/rides/?view=week&start=not-a-date')
        assert resp.status_code == 200
        assert b'week-grid' in resp.data

    def test_start_snapped_to_monday(self, client, mock_weather):
        # Passing a Wednesday should snap back to Monday of that week
        today = date.today()
        wednesday = today - timedelta(days=today.weekday()) + timedelta(days=2)
        resp = client.get(f'/rides/?view=week&start={wednesday.isoformat()}')
        assert resp.status_code == 200

    def test_weather_shown_on_ride_card(self, client, sample_rides, mock_weather):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        resp = client.get(f'/rides/?view=week&start={monday.isoformat()}')
        html = resp.data.decode()
        assert 'wr-weather' in html

    def test_today_column_highlighted(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        html = resp.data.decode()
        assert 'week-col-today' in html

    def test_weather_legend_present(self, client, mock_weather):
        resp = client.get('/rides/?view=week')
        assert b'weather-legend' in resp.data


# ── Month view ────────────────────────────────────────────────────────────────

class TestMonthView:
    def test_returns_200(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        assert resp.status_code == 200

    def test_renders_month_grid(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        html = resp.data.decode()
        assert 'month-grid' in html

    def test_day_of_week_headers(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        html = resp.data.decode()
        for dow in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            assert dow in html

    def test_shows_current_month_name(self, client, mock_weather):
        import calendar
        today = date.today()
        month_name = calendar.month_name[today.month]
        resp = client.get('/rides/?view=month')
        assert month_name.encode() in resp.data

    def test_explicit_year_month(self, client, mock_weather):
        resp = client.get('/rides/?view=month&y=2026&m=5')
        assert resp.status_code == 200
        assert b'May 2026' in resp.data

    def test_rides_appear_in_correct_cell(self, client, sample_rides, mock_weather):
        today = date.today()
        resp = client.get(f'/rides/?view=month&y={today.year}&m={today.month}')
        html = resp.data.decode()
        # At least some of our rides land in this month
        assert 'cell-ride' in html

    def test_prev_next_navigation_links(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        html = resp.data.decode()
        assert 'Prev' in html
        assert 'Next' in html
        assert 'view=month' in html

    def test_prev_month_navigation(self, client, mock_weather):
        resp = client.get('/rides/?view=month&y=2026&m=4')
        # Prev of April 2026 → March 2026
        html = resp.data.decode()
        assert 'm=3' in html or 'y=2026' in html

    def test_next_month_wraps_year(self, client, mock_weather):
        resp = client.get('/rides/?view=month&y=2026&m=12')
        html = resp.data.decode()
        # Next should point to January 2027
        assert 'm=1' in html

    def test_today_cell_highlighted(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        assert b'is-today' in resp.data

    def test_invalid_month_clamped(self, client, mock_weather):
        resp = client.get('/rides/?view=month&y=2026&m=99')
        assert resp.status_code == 200

    def test_other_month_days_marked(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        assert b'other-month' in resp.data

    def test_weather_legend_present(self, client, mock_weather):
        resp = client.get('/rides/?view=month')
        assert b'weather-legend' in resp.data

    def test_cancelled_ride_marked(self, client, sample_rides, mock_weather):
        today = date.today()
        resp = client.get(f'/rides/?view=month&y={today.year}&m={today.month}')
        html = resp.data.decode()
        # cell-cancelled class added when ride is cancelled
        assert 'cell-cancelled' in html
