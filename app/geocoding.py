"""
Zip code geocoding via Nominatim (OpenStreetMap).
Returns (lat, lng) for a US zip code, or None on failure.
"""
import math
import requests


NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_HEADERS = {'User-Agent': 'CyclingClubs/1.0 (cyclingclub.pcp.dev)'}


def geocode_zip(zip_code: str):
    """Return (lat, lng) for a US zip code, or None if not found."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={'postalcode': zip_code, 'country': 'US', 'format': 'json', 'limit': 1},
            headers=NOMINATIM_HEADERS,
            timeout=5,
        )
        results = resp.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except Exception:
        pass
    return None


def haversine_miles(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def clubs_near_zip(zip_code: str, clubs, radius_miles: float = 50):
    """
    Given a list of Club objects (with lat/lng), return those within radius_miles
    of the zip code, sorted by distance. Returns (list_of_(club, distance), error_msg).
    """
    coords = geocode_zip(zip_code)
    if coords is None:
        return [], 'Could not locate that zip code.'

    lat, lng = coords
    results = []
    for club in clubs:
        if club.lat is not None and club.lng is not None:
            dist = haversine_miles(lat, lng, club.lat, club.lng)
            if dist <= radius_miles:
                results.append((club, round(dist, 1)))

    results.sort(key=lambda x: x[1])
    return results, None
