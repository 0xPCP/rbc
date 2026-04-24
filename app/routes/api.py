"""
JSON API endpoints — used by client-side JS.
"""
from flask import Blueprint, jsonify, request
from ..weather import get_current_weather
from ..gear import cycling_gear, VERDICT_LABEL
from ..geocoding import geocode_zip

api_bp = Blueprint('api', __name__)


@api_bp.route('/weather/widget')
def weather_widget():
    """
    GET /api/weather/widget?lat=X&lng=Y
    GET /api/weather/widget?zip=XXXXX

    Returns current conditions + cycling gear recommendations as JSON.
    """
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    zip_code = request.args.get('zip', '').strip()

    if lat is None or lng is None:
        if zip_code:
            coords = geocode_zip(zip_code)
            if coords is None:
                return jsonify({'error': 'Could not locate zip code.'}), 400
            lat, lng = coords
        else:
            return jsonify({'error': 'Provide lat/lng or zip.'}), 400

    weather = get_current_weather(lat, lng)
    if weather is None:
        return jsonify({'error': 'Weather service unavailable.'}), 503

    gear = cycling_gear(
        temp_f=weather['temp_f'],
        feels_like_f=weather['feels_like_f'],
        wind_mph=weather['wind_mph'],
        precip_prob=weather['precip_prob'],
        weather_code=weather['weather_code'],
    )

    verdict_text, verdict_class = VERDICT_LABEL[gear['verdict']]

    gear_items = []
    for key, icon in [
        ('bottoms',     '🩳'),
        ('top',         '👕'),
        ('base_layer',  '🧥'),
        ('outer_layer', '🧥'),
        ('gloves',      '🧤'),
        ('head',        '🧢'),
        ('feet',        '👟'),
    ]:
        val = gear.get(key)
        if val:
            gear_items.append({'icon': icon, 'label': val})
    for extra in gear.get('extras', []):
        gear_items.append({'icon': '💡', 'label': extra})

    return jsonify({
        'temp_f':       weather['temp_f'],
        'feels_like_f': weather['feels_like_f'],
        'wind_mph':     weather['wind_mph'],
        'precip_prob':  weather['precip_prob'],
        'description':  weather['description'],
        'emoji':        weather['emoji'],
        'severity':     weather['severity'],
        'verdict':      gear['verdict'],
        'verdict_text': verdict_text,
        'verdict_class': verdict_class,
        'gear':         gear_items,
        'location_used': f'{round(lat, 3)}, {round(lng, 3)}',
    })
