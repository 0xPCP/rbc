"""Shared utility helpers."""
import re

_HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


def is_valid_hex(color):
    return bool(color and _HEX_RE.match(color))


def _clamp(v):
    return max(0, min(255, int(v)))


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(_clamp(r), _clamp(g), _clamp(b))


def _mix_white(hex_color, amount):
    """Blend toward white. amount 0.0 = original, 1.0 = white."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)


def _mix_black(hex_color, amount):
    """Blend toward black. amount 0.0 = original, 1.0 = black."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r * (1 - amount), g * (1 - amount), b * (1 - amount))


def club_theme_vars(club):
    """
    Return a dict of CSS custom property overrides for a club's theme.
    Keys are CSS variable names (e.g. '--rbc-green-dark'), values are hex strings.
    Returns an empty dict when no theme is set.
    """
    result = {}

    if club.theme_primary and is_valid_hex(club.theme_primary):
        p = club.theme_primary.lower()
        result['--rbc-green-dark']  = _mix_black(p, 0.30)
        result['--rbc-green']       = p
        result['--rbc-green-light'] = _mix_white(p, 0.38)
        result['--rbc-green-pale']  = _mix_white(p, 0.82)

    if club.theme_accent and is_valid_hex(club.theme_accent):
        a = club.theme_accent.lower()
        result['--rbc-orange']      = a
        result['--rbc-orange-dark'] = _mix_black(a, 0.15)

    return result
