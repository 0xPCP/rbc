"""Security-focused validation helpers."""
import re
from urllib.parse import parse_qs, unquote, urlparse


_DANGEROUS_URL_CHARS = re.compile(r'[\x00-\x1f\x7f<>"\'`()\\]')
_YOUTUBE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{6,64}$')
_VIMEO_ID_RE = re.compile(r'^\d{6,18}$')
_STRAVA_ACTIVITY_RE = re.compile(r'^/activities/\d+/?$')


def is_safe_external_url(value):
    """Accept only plain http(s) URLs safe for HTML attributes and CSS-adjacent use."""
    if not value:
        return False
    value = value.strip()
    decoded = unquote(value)
    if _DANGEROUS_URL_CHARS.search(value) or _DANGEROUS_URL_CHARS.search(decoded):
        return False

    parsed = urlparse(value)
    return (
        parsed.scheme.lower() in ('http', 'https')
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
    )


def video_embed_url(value):
    """Return a safe embed URL for supported video providers, otherwise None."""
    if not is_safe_external_url(value):
        return None

    parsed = urlparse(value)
    host = parsed.hostname.lower() if parsed.hostname else ''
    path = parsed.path or ''

    if host in ('youtube.com', 'www.youtube.com') and path == '/watch':
        video_id = parse_qs(parsed.query).get('v', [''])[0]
        if _YOUTUBE_ID_RE.match(video_id):
            return f'https://www.youtube.com/embed/{video_id}'

    if host == 'youtu.be':
        video_id = path.strip('/').split('/', 1)[0]
        if _YOUTUBE_ID_RE.match(video_id):
            return f'https://www.youtube.com/embed/{video_id}'

    if host in ('vimeo.com', 'www.vimeo.com'):
        video_id = path.strip('/').split('/', 1)[0]
        if _VIMEO_ID_RE.match(video_id):
            return f'https://player.vimeo.com/video/{video_id}'

    return None


def is_allowed_video_link(value):
    """Allow supported video links, including non-embeddable Strava activities."""
    if video_embed_url(value):
        return True
    if not is_safe_external_url(value):
        return False
    parsed = urlparse(value)
    host = parsed.hostname.lower() if parsed.hostname else ''
    return host in ('strava.com', 'www.strava.com') and bool(_STRAVA_ACTIVITY_RE.match(parsed.path or ''))
