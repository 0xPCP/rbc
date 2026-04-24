"""
Cycling gear recommendations based on current weather conditions.
Ported from the weatherapp project (weatherapp/src/gear.py).

Uses a two-temperature model:
  start_fl  = apparent (feels-like) temperature — what extremities feel at start
  core_fl   = start_fl + 12°F — what the body core reaches during effort
"""


_RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 85, 86, 95, 96, 99}


def cycling_gear(temp_f: float, feels_like_f: float, wind_mph: float,
                 precip_prob: int, weather_code: int) -> dict:
    """
    Return a structured gear recommendation dict.

    Keys:
        verdict      str   'great' | 'go' | 'marginal' | 'skip'
        bottoms      str
        top          str
        base_layer   str | None
        outer_layer  str | None
        gloves       str | None
        head         str | None
        feet         str | None
        extras       list[str]   sunscreen, etc.
    """
    core_fl  = feels_like_f + 12
    start_fl = feels_like_f
    raining  = weather_code in _RAIN_CODES and precip_prob >= 30

    # ── Verdict ──────────────────────────────────────────────────────────────
    snow = weather_code in {71, 73, 75, 77, 85, 86}
    if snow or temp_f < 20 or precip_prob >= 70 or wind_mph >= 32:
        verdict = 'skip'
    elif temp_f < 32 or precip_prob >= 45 or wind_mph >= 20 or raining:
        verdict = 'marginal'
    elif precip_prob <= 10 and wind_mph <= 12 and 58 <= feels_like_f <= 80:
        verdict = 'great'
    else:
        verdict = 'go'

    # ── Bottoms ───────────────────────────────────────────────────────────────
    if core_fl >= 68:
        bottoms = 'Bib shorts'
    elif core_fl >= 55:
        bottoms = 'Bib knickers'
    elif core_fl >= 42:
        bottoms = 'Bib tights'
    else:
        bottoms = 'Thermal bib tights'

    # ── Top ───────────────────────────────────────────────────────────────────
    if core_fl >= 62:
        top = 'Short-sleeve jersey'
    elif core_fl >= 48:
        top = 'Long-sleeve jersey'
    else:
        top = 'Thermal long-sleeve jersey'

    # ── Base layer ────────────────────────────────────────────────────────────
    if core_fl < 50:
        base_layer = 'Thermal base layer'
    elif core_fl < 62:
        base_layer = 'Light base layer'
    else:
        base_layer = None

    # ── Outer layer ───────────────────────────────────────────────────────────
    if raining:
        outer_layer = 'Rain jacket'
    elif start_fl < 28:
        outer_layer = 'Insulated jacket'
    elif start_fl < 45:
        outer_layer = 'Cycling jacket'
    elif wind_mph >= 20 and start_fl < 62:
        outer_layer = 'Wind vest'
    else:
        outer_layer = None

    # ── Gloves ────────────────────────────────────────────────────────────────
    if start_fl < 25:
        gloves = 'Warm winter gloves'
    elif start_fl < 42:
        gloves = 'Full-finger gloves'
    elif start_fl < 55:
        gloves = 'Light gloves'
    elif start_fl < 72:
        gloves = 'Fingerless gloves'
    else:
        gloves = None

    # ── Head ──────────────────────────────────────────────────────────────────
    if start_fl < 22:
        head = 'Balaclava + neck gaiter'
    elif start_fl < 35:
        head = 'Skull cap'
    elif start_fl < 55:
        head = 'Ear covers'
    else:
        head = None

    # ── Feet ──────────────────────────────────────────────────────────────────
    if start_fl < 22:
        feet = 'Insulated booties'
    elif start_fl < 38:
        feet = 'Booties'
    elif start_fl < 56:
        feet = 'Shoe covers'
    else:
        feet = None

    # ── Extras ────────────────────────────────────────────────────────────────
    extras = []
    if weather_code <= 1 and temp_f >= 60:
        extras.append('Sunscreen + sunglasses')
    if precip_prob >= 30 and not raining:
        extras.append('Consider a gilet or cape — rain possible')

    return {
        'verdict':     verdict,
        'bottoms':     bottoms,
        'top':         top,
        'base_layer':  base_layer,
        'outer_layer': outer_layer,
        'gloves':      gloves,
        'head':        head,
        'feet':        feet,
        'extras':      extras,
    }


VERDICT_LABEL = {
    'great':    ('Great day to ride!',      'success'),
    'go':       ('Good to go.',             'primary'),
    'marginal': ('Rideable — dress right.', 'warning'),
    'skip':     ('Consider skipping.',      'danger'),
}
