"""
Tests for gear recommendations and the /api/weather/widget endpoint.
"""
import pytest
from unittest.mock import patch
from app.gear import cycling_gear, VERDICT_LABEL

MOCK_WEATHER = {
    'temp_f': 65, 'feels_like_f': 62, 'wind_mph': 8,
    'precip_prob': 5, 'weather_code': 1,
    'description': 'Mainly clear', 'emoji': '🌤️', 'severity': 0,
}


# ── Gear logic ────────────────────────────────────────────────────────────────

class TestCyclingGear:
    def test_warm_day_bib_shorts(self):
        g = cycling_gear(75, 72, 5, 5, 0)
        assert g['bottoms'] == 'Bib shorts'
        assert g['verdict'] == 'great'

    def test_cold_day_thermal_tights(self):
        g = cycling_gear(30, 28, 10, 10, 0)
        assert 'thermal' in g['bottoms'].lower()
        assert g['verdict'] in ('marginal', 'skip')

    def test_rain_triggers_rain_jacket(self):
        g = cycling_gear(60, 58, 10, 60, 61)  # rain code + 60% precip
        assert g['outer_layer'] == 'Rain jacket'

    def test_no_gloves_on_hot_day(self):
        g = cycling_gear(85, 82, 5, 0, 0)
        assert g['gloves'] is None

    def test_full_finger_gloves_when_cold(self):
        g = cycling_gear(45, 40, 10, 5, 0)
        assert 'gloves' in g['gloves'].lower()

    def test_skip_verdict_on_ice(self):
        g = cycling_gear(28, 18, 5, 0, 73)  # snow code
        assert g['verdict'] == 'skip'

    def test_skip_verdict_high_wind(self):
        g = cycling_gear(60, 58, 35, 5, 0)
        assert g['verdict'] == 'skip'

    def test_marginal_verdict_rain_likely(self):
        g = cycling_gear(55, 52, 10, 50, 61)
        assert g['verdict'] == 'marginal'

    def test_base_layer_when_cold(self):
        g = cycling_gear(42, 38, 8, 5, 0)
        assert g['base_layer'] is not None

    def test_no_base_layer_when_warm(self):
        g = cycling_gear(80, 78, 5, 0, 0)
        assert g['base_layer'] is None

    def test_sunscreen_on_clear_warm_day(self):
        g = cycling_gear(75, 72, 5, 0, 0)
        assert any('sunscreen' in e.lower() for e in g['extras'])

    @pytest.mark.parametrize('verdict', ['great', 'go', 'marginal', 'skip'])
    def test_all_verdicts_have_labels(self, verdict):
        assert verdict in VERDICT_LABEL
        text, cls = VERDICT_LABEL[verdict]
        assert text and cls


# ── API endpoint ──────────────────────────────────────────────────────────────

class TestWeatherWidgetApi:
    def test_returns_200_with_lat_lng(self, client):
        with patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            resp = client.get('/api/weather/widget?lat=38.9&lng=-77.3')
        assert resp.status_code == 200

    def test_returns_json(self, client):
        with patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            resp = client.get('/api/weather/widget?lat=38.9&lng=-77.3')
        assert resp.is_json

    def test_response_contains_gear(self, client):
        with patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            data = client.get('/api/weather/widget?lat=38.9&lng=-77.3').get_json()
        assert 'gear' in data
        assert isinstance(data['gear'], list)

    def test_response_contains_verdict(self, client):
        with patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            data = client.get('/api/weather/widget?lat=38.9&lng=-77.3').get_json()
        assert data['verdict'] in ('great', 'go', 'marginal', 'skip')

    def test_zip_param_geocodes(self, client):
        with patch('app.routes.api.geocode_zip', return_value=(38.9, -77.3)), \
             patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            resp = client.get('/api/weather/widget?zip=20191')
        assert resp.status_code == 200

    def test_bad_zip_returns_400(self, client):
        with patch('app.routes.api.geocode_zip', return_value=None):
            resp = client.get('/api/weather/widget?zip=00000')
        assert resp.status_code == 400

    def test_missing_params_returns_400(self, client):
        resp = client.get('/api/weather/widget')
        assert resp.status_code == 400

    def test_weather_service_failure_returns_503(self, client):
        with patch('app.routes.api.get_current_weather', return_value=None):
            resp = client.get('/api/weather/widget?lat=38.9&lng=-77.3')
        assert resp.status_code == 503
