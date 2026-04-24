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

    def test_rain_triggers_rain_cape(self):
        g = cycling_gear(60, 58, 10, 60, 61)  # rain code + 60% precip
        assert g['outer'] == 'Rain cape'

    def test_no_gloves_on_hot_day(self):
        g = cycling_gear(85, 82, 5, 0, 0)
        assert g['gloves'] is None

    def test_gloves_when_cold(self):
        g = cycling_gear(45, 40, 10, 5, 0)
        assert g['gloves'] is not None

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

    def test_sunglasses_on_clear_warm_day(self):
        g = cycling_gear(75, 72, 5, 0, 0)
        assert g['eyewear'] == 'Sunglasses'

    def test_warmers_list_returned(self):
        g = cycling_gear(60, 57, 5, 5, 0)  # core_fl = 57+12=69, start_fl=57 — no warmers
        assert isinstance(g['warmers'], list)

    def test_arm_warmers_in_range(self):
        # core_fl = 55+12 = 67, so arm warmers range (50-65) — wait, 67 is outside
        # Let's use feels_like=48 so core_fl=60, which is in 50<=core_fl<65
        g = cycling_gear(55, 48, 5, 5, 0)
        warmer_labels = [w.lower() for w in g['warmers']]
        assert any('arm' in w for w in warmer_labels)

    def test_inventory_filters_gear(self):
        # Only owns bib-shorts and jersey — should get those on a warm day
        g = cycling_gear(75, 72, 5, 5, 0, owned_ids=['bib-shorts', 'jersey'])
        assert g['bottoms'] == 'Bib shorts'
        assert g['jersey'] == 'Regular jersey'

    def test_inventory_fallback_when_not_owned(self):
        # Owns only thermal-bib-tights; warm day prefers bib-shorts but user doesn't own it
        g = cycling_gear(75, 72, 5, 5, 0, owned_ids=['thermal-bib-tights'])
        assert g['bottoms'] == 'Thermal bib tights'

    def test_no_inventory_returns_ideal(self):
        # owned_ids=None → always return first (ideal) item
        g = cycling_gear(75, 72, 5, 5, 0, owned_ids=None)
        assert g['bottoms'] == 'Bib shorts'

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

    def test_gear_list_has_icon_and_label(self, client):
        with patch('app.routes.api.get_current_weather', return_value=MOCK_WEATHER):
            data = client.get('/api/weather/widget?lat=38.9&lng=-77.3').get_json()
        for item in data['gear']:
            assert 'icon' in item
            assert 'label' in item
