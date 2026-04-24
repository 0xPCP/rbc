"""
Weather for RBC rides using the Open-Meteo API (free, no API key required).
Makes one bulk API call per page view covering all rides in the displayed range.
Results cached for 30 minutes.
"""
import time
import requests
from datetime import date, datetime, timezone

# All RBC rides are within a ~5-mile radius — one forecast point covers everything.
# Reston, VA centroid.
_LAT = 38.9586
_LNG = -77.3570

# WMO weather interpretation codes → (label, emoji, base_severity)
# severity: 0 = good, 1 = caution, 2 = warning
_WMO = {
    0:  ('Clear',           '☀️',  0),
    1:  ('Mainly clear',    '🌤️', 0),
    2:  ('Partly cloudy',   '⛅',  0),
    3:  ('Overcast',        '☁️',  1),
    45: ('Fog',             '🌫️', 1),
    48: ('Freezing fog',    '🌫️', 1),
    51: ('Light drizzle',   '🌦️', 1),
    53: ('Drizzle',         '🌦️', 1),
    55: ('Heavy drizzle',   '🌧️', 2),
    61: ('Light rain',      '🌧️', 2),
    63: ('Rain',            '🌧️', 2),
    65: ('Heavy rain',      '🌧️', 2),
    71: ('Light snow',      '❄️',  2),
    73: ('Snow',            '❄️',  2),
    75: ('Heavy snow',      '❄️',  2),
    77: ('Snow grains',     '❄️',  2),
    80: ('Rain showers',    '🌧️', 2),
    81: ('Rain showers',    '🌧️', 2),
    82: ('Heavy showers',   '🌧️', 2),
    85: ('Snow showers',    '❄️',  2),
    86: ('Heavy snow',      '❄️',  2),
    95: ('Thunderstorm',    '⛈️',  2),
    96: ('Thunderstorm',    '⛈️',  2),
    99: ('Thunderstorm',    '⛈️',  2),
}

# Cache: key → {hourly: {...}, _ts: float}
_cache = {}


def get_weather_for_rides(rides):
    """
    Return {ride.id: weather_dict} for rides within the next 14 days.

    Weather dict keys:
        description  str     human-readable condition label
        emoji        str     WMO condition emoji
        severity     int     0=good, 1=caution, 2=warning
        temp_f       int     temperature in °F
        wind_mph     int     wind speed in mph
        precip_prob  int     precipitation probability 0-100
        warning      bool    True if cycling conditions are poor
        warning_reasons  list[str]
    """
    today = date.today()
    in_window = [r for r in rides if 0 <= (r.date - today).days <= 14]
    if not in_window:
        return {}

    dates = sorted({r.date for r in in_window})
    forecast_days = min((dates[-1] - today).days + 2, 16)

    cache_key = (dates[0].isoformat(), forecast_days)
    now = time.time()

    if cache_key in _cache and now - _cache[cache_key]['_ts'] < 1800:
        hourly = _cache[cache_key]['hourly']
    else:
        try:
            resp = requests.get(
                'https://api.open-meteo.com/v1/forecast',
                params={
                    'latitude':        _LAT,
                    'longitude':       _LNG,
                    'hourly':          'temperature_2m,precipitation_probability,precipitation,wind_speed_10m,weather_code',
                    'temperature_unit':'fahrenheit',
                    'wind_speed_unit': 'mph',
                    'forecast_days':   forecast_days,
                    'timezone':        'America/New_York',
                },
                timeout=10,
            )
            data = resp.json()
        except Exception:
            return {}

        hourly = {}
        for i, t in enumerate(data['hourly']['time']):
            hourly[t] = {
                'temp_f':      round(data['hourly']['temperature_2m'][i]),
                'precip_prob': data['hourly']['precipitation_probability'][i] or 0,
                'precip_mm':   data['hourly']['precipitation'][i] or 0,
                'wind_mph':    round(data['hourly']['wind_speed_10m'][i]),
                'code':        data['hourly']['weather_code'][i],
            }
        _cache[cache_key] = {'hourly': hourly, '_ts': now}

    result = {}
    for ride in in_window:
        key = f"{ride.date.isoformat()}T{ride.time.hour:02d}:00"
        h = hourly.get(key)
        if not h:
            continue

        desc, emoji, code_sev = _WMO.get(h['code'], ('Unknown', '❓', 1))

        warnings = []
        if h['precip_prob'] >= 60 and h['precip_mm'] >= 1:
            warnings.append(f"{h['precip_prob']}% chance of rain")
        if h['wind_mph'] >= 25:
            warnings.append(f"{h['wind_mph']} mph winds")
        if h['temp_f'] <= 35:
            warnings.append(f"{h['temp_f']}°F — dress in layers")
        if h['temp_f'] >= 95:
            warnings.append(f"{h['temp_f']}°F — extreme heat")
        if h['code'] >= 95:
            warnings.append('thunderstorm possible')

        if warnings:
            sev = max(code_sev, 2)
        elif h['precip_prob'] >= 30 or h['wind_mph'] >= 15 or h['temp_f'] <= 45 or h['temp_f'] >= 88:
            sev = max(code_sev, 1)
        else:
            sev = code_sev

        result[ride.id] = {
            'description':    desc,
            'emoji':          emoji,
            'severity':       sev,
            'temp_f':         h['temp_f'],
            'wind_mph':       h['wind_mph'],
            'precip_prob':    h['precip_prob'],
            'warning':        bool(warnings),
            'warning_reasons': warnings,
        }

    return result


# Cache for current-conditions widget: key=(lat_r, lng_r) → {data, _ts}
_widget_cache = {}


def get_current_weather(lat: float, lng: float) -> dict | None:
    """
    Fetch current-hour weather for an arbitrary lat/lng.
    Returns a dict with temp_f, feels_like_f, wind_mph, precip_prob,
    weather_code, description, emoji, severity — or None on failure.
    Cached 15 minutes per location (rounded to 2 decimal places).
    """
    key = (round(lat, 2), round(lng, 2))
    now = time.time()
    if key in _widget_cache and now - _widget_cache[key]['_ts'] < 900:
        return _widget_cache[key]['data']

    try:
        resp = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude':         lat,
                'longitude':        lng,
                'current':          'temperature_2m,apparent_temperature,precipitation_probability,wind_speed_10m,weather_code',
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit':  'mph',
                'timezone':         'auto',
            },
            timeout=8,
        )
        c = resp.json().get('current', {})
    except Exception:
        return None

    code = c.get('weather_code', 0)
    desc, emoji, sev = _WMO.get(code, ('Unknown', '❓', 1))

    data = {
        'temp_f':       round(c.get('temperature_2m', 0)),
        'feels_like_f': round(c.get('apparent_temperature', 0)),
        'wind_mph':     round(c.get('wind_speed_10m', 0)),
        'precip_prob':  c.get('precipitation_probability') or 0,
        'weather_code': code,
        'description':  desc,
        'emoji':        emoji,
        'severity':     sev,
    }
    _widget_cache[key] = {'data': data, '_ts': now}
    return data
