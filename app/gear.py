"""
Cycling gear recommendations based on current weather conditions.
Ported from weatherapp — uses the same gear catalog, pickFirst() logic,
and two-temperature model.

owned_ids: set of gear item IDs the user owns. If None, returns ideal items
           regardless of inventory (used when no inventory is configured).
"""

_RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 85, 86, 95, 96, 99}

# ── Gear catalog ──────────────────────────────────────────────────────────────
# Ordered warm→cold within each category (same order as weatherapp).

GEAR_CATALOG = {
    'Bottoms': [
        {'id': 'bib-shorts',         'label': 'Bib shorts'},
        {'id': 'bib-knickers',       'label': 'Bib knickers'},
        {'id': 'bib-tights',         'label': 'Bib tights'},
        {'id': 'thermal-bib-tights', 'label': 'Thermal bib tights'},
    ],
    'Base Layers': [
        {'id': 'base-light',   'label': 'Light base layer'},
        {'id': 'base-mid',     'label': 'Mid-weight base layer'},
        {'id': 'base-thermal', 'label': 'Thermal base layer'},
        {'id': 'base-heavy',   'label': 'Heavy base layer'},
    ],
    'Jersey': [
        {'id': 'jersey-light',   'label': 'Lightweight jersey'},
        {'id': 'jersey',         'label': 'Regular jersey'},
        {'id': 'jersey-ls',      'label': 'Long-sleeve jersey'},
        {'id': 'jersey-thermal', 'label': 'Thermal long-sleeve jersey'},
    ],
    'Warmers': [
        {'id': 'arm-warmers',  'label': 'Arm warmers'},
        {'id': 'knee-warmers', 'label': 'Knee warmers'},
        {'id': 'leg-warmers',  'label': 'Leg warmers'},
    ],
    'Outerwear': [
        {'id': 'wind-vest',        'label': 'Wind vest'},
        {'id': 'wind-jacket',      'label': 'Wind jacket'},
        {'id': 'rain-cape',        'label': 'Rain cape'},
        {'id': 'jacket',           'label': 'Cycling jacket'},
        {'id': 'insulated-jacket', 'label': 'Insulated jacket'},
    ],
    'Gloves': [
        {'id': 'gloves-fingerless', 'label': 'Fingerless gloves'},
        {'id': 'gloves-light',      'label': 'Light gloves'},
        {'id': 'gloves-medium',     'label': 'Medium gloves'},
        {'id': 'gloves-full',       'label': 'Full-finger gloves'},
        {'id': 'gloves-warm',       'label': 'Warm winter gloves'},
    ],
    'Head & Neck': [
        {'id': 'ear-covers',   'label': 'Ear covers'},
        {'id': 'skull-cap',    'label': 'Skull cap'},
        {'id': 'neck-gaiter',  'label': 'Neck gaiter'},
        {'id': 'helmet-cover', 'label': 'Helmet cover'},
        {'id': 'balaclava',    'label': 'Balaclava'},
    ],
    'Feet': [
        {'id': 'shoe-covers',       'label': 'Shoe covers'},
        {'id': 'booties',           'label': 'Booties'},
        {'id': 'insulated-booties', 'label': 'Insulated booties'},
    ],
    'Eyewear': [
        {'id': 'sunglasses',   'label': 'Sunglasses'},
        {'id': 'clear-lenses', 'label': 'Clear lenses'},
    ],
}

# Flat id→label lookup
_LABEL = {item['id']: item['label']
          for items in GEAR_CATALOG.values() for item in items}

ALL_ITEM_IDS = list(_LABEL.keys())


def _pick(owned, *ids):
    """
    Return the label of the first item from `ids` that the user owns.
    If owned is None (no inventory configured) return the first item unconditionally.
    Returns None if the user owns none of the listed items.
    """
    for item_id in ids:
        if owned is None or item_id in owned:
            return _LABEL[item_id]
    return None


# ── Main recommendation function ──────────────────────────────────────────────

def cycling_gear(temp_f: float, feels_like_f: float, wind_mph: float,
                 precip_prob: int, weather_code: int,
                 owned_ids=None) -> dict:
    """
    Return gear recommendations filtered to items the user owns.

    owned_ids: collection of gear item IDs the user owns, or None to ignore
               inventory and always return the ideal item.
    """
    owned = set(owned_ids) if owned_ids is not None else None
    core_fl  = feels_like_f + 12   # body warms up during effort
    start_fl = feels_like_f        # extremities feel ambient at start
    raining  = weather_code in _RAIN_CODES and precip_prob >= 30

    # ── Verdict ───────────────────────────────────────────────────────────────
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
        bottoms = _pick(owned, 'bib-shorts', 'bib-knickers', 'bib-tights', 'thermal-bib-tights')
    elif core_fl >= 55:
        bottoms = _pick(owned, 'bib-knickers', 'bib-tights', 'bib-shorts', 'thermal-bib-tights')
    elif core_fl >= 42:
        bottoms = _pick(owned, 'bib-tights', 'thermal-bib-tights', 'bib-knickers')
    else:
        bottoms = _pick(owned, 'thermal-bib-tights', 'bib-tights', 'bib-knickers')

    # ── Jersey ────────────────────────────────────────────────────────────────
    if core_fl >= 75:
        jersey = _pick(owned, 'jersey-light', 'jersey', 'jersey-ls', 'jersey-thermal')
    elif core_fl >= 62:
        jersey = _pick(owned, 'jersey', 'jersey-light', 'jersey-ls', 'jersey-thermal')
    elif core_fl >= 48:
        jersey = _pick(owned, 'jersey-ls', 'jersey-thermal', 'jersey', 'jersey-light')
    else:
        jersey = _pick(owned, 'jersey-thermal', 'jersey-ls', 'jersey', 'jersey-light')

    # ── Base layer ────────────────────────────────────────────────────────────
    if core_fl < 38:
        base_layer = _pick(owned, 'base-heavy', 'base-thermal', 'base-mid', 'base-light')
    elif core_fl < 50:
        base_layer = _pick(owned, 'base-thermal', 'base-mid', 'base-heavy', 'base-light')
    elif core_fl < 62:
        base_layer = _pick(owned, 'base-mid', 'base-light', 'base-thermal')
    else:
        base_layer = None  # no base needed

    # ── Warmers (arm/knee/leg) ────────────────────────────────────────────────
    warmers = []
    if 50 <= core_fl < 65:
        w = _pick(owned, 'arm-warmers')
        if w:
            warmers.append(w)
    if 45 <= core_fl < 55:
        w = _pick(owned, 'knee-warmers', 'leg-warmers')
        if w:
            warmers.append(w)
    if core_fl < 45:
        w = _pick(owned, 'leg-warmers', 'knee-warmers')
        if w:
            warmers.append(w)

    # ── Outerwear ─────────────────────────────────────────────────────────────
    if raining:
        outer = _pick(owned, 'rain-cape', 'jacket', 'wind-jacket', 'insulated-jacket')
    elif start_fl < 28:
        outer = _pick(owned, 'insulated-jacket', 'jacket', 'wind-jacket')
    elif start_fl < 45:
        outer = _pick(owned, 'jacket', 'wind-jacket', 'insulated-jacket')
    elif wind_mph >= 20 and start_fl < 62:
        outer = _pick(owned, 'wind-vest', 'wind-jacket', 'jacket')
    elif start_fl < 58:
        outer = _pick(owned, 'wind-vest', 'wind-jacket')
    else:
        outer = None

    # ── Gloves ────────────────────────────────────────────────────────────────
    if start_fl < 25:
        gloves = _pick(owned, 'gloves-warm', 'gloves-full', 'gloves-medium')
    elif start_fl < 38:
        gloves = _pick(owned, 'gloves-full', 'gloves-warm', 'gloves-medium', 'gloves-light')
    elif start_fl < 50:
        gloves = _pick(owned, 'gloves-medium', 'gloves-full', 'gloves-light', 'gloves-fingerless')
    elif start_fl < 62:
        gloves = _pick(owned, 'gloves-light', 'gloves-medium', 'gloves-fingerless')
    elif start_fl < 72:
        gloves = _pick(owned, 'gloves-fingerless', 'gloves-light')
    else:
        gloves = None

    # ── Head & neck ───────────────────────────────────────────────────────────
    if start_fl < 22:
        head = _pick(owned, 'balaclava', 'neck-gaiter', 'skull-cap', 'helmet-cover')
    elif start_fl < 35:
        head = _pick(owned, 'skull-cap', 'balaclava', 'ear-covers', 'helmet-cover')
    elif start_fl < 50:
        head = _pick(owned, 'ear-covers', 'skull-cap', 'helmet-cover')
    else:
        head = None

    # ── Feet ──────────────────────────────────────────────────────────────────
    if start_fl < 22:
        feet = _pick(owned, 'insulated-booties', 'booties', 'shoe-covers')
    elif start_fl < 38:
        feet = _pick(owned, 'booties', 'insulated-booties', 'shoe-covers')
    elif start_fl < 56:
        feet = _pick(owned, 'shoe-covers', 'booties', 'insulated-booties')
    else:
        feet = None

    # ── Eyewear ───────────────────────────────────────────────────────────────
    if weather_code <= 1 and temp_f >= 55:
        eyewear = _pick(owned, 'sunglasses', 'clear-lenses')
    elif weather_code >= 61 or weather_code == 45:
        eyewear = _pick(owned, 'clear-lenses', 'sunglasses')
    else:
        eyewear = None

    return {
        'verdict':    verdict,
        'bottoms':    bottoms,
        'jersey':     jersey,
        'base_layer': base_layer,
        'warmers':    warmers,
        'outer':      outer,
        'gloves':     gloves,
        'head':       head,
        'feet':       feet,
        'eyewear':    eyewear,
    }


VERDICT_LABEL = {
    'great':    ('Great day to ride!',      'success'),
    'go':       ('Good to go.',             'primary'),
    'marginal': ('Rideable — dress right.', 'warning'),
    'skip':     ('Consider skipping.',      'danger'),
}

# Gear item → display icon (for the widget)
ITEM_ICONS = {
    'Bottoms':    '🩳',
    'Jersey':     '👕',
    'Base Layers':'🧥',
    'Warmers':    '💪',
    'Outerwear':  '🧥',
    'Gloves':     '🧤',
    'Head & Neck':'🧢',
    'Feet':       '👟',
    'Eyewear':    '🕶️',
}
