# Cycling Clubs App — CLAUDE.md

## What this project is

A multi-tenant cycling club platform where any cycling club can host their club page, manage a weekly ride calendar, and publish rides. Users register once, subscribe to clubs, and see all their upcoming rides across every club on a single home screen.

The current codebase started as a single-club app (Reston Bike Club). It is being generalized into the multi-tenant platform described here.

## Tech stack

- **Backend:** Python / Flask + gunicorn
- **Database:** PostgreSQL (Flask-SQLAlchemy)
- **Auth:** Flask-Login + Flask-Bcrypt (future: OAuth via Google/Microsoft)
- **Forms:** Flask-WTF / WTForms
- **Weather:** Open-Meteo API (self-hosted logic ported from the `weatherapp` project)
- **Maps:** RideWithGPS embeds; club/ride discovery map TBD (Leaflet + OpenStreetMap preferred)
- **Containerization:** Docker, deployed on TrueNAS Scale

## Repository & deployment

- **Local dev / source of truth:** `D:\Projects\rbc\`
- **Dev platform:** TrueNAS Scale at `192.168.50.189` via Docker Compose
- **Dev URL:** `cyclingclub.pcp.dev` (Cloudflare Tunnel)
- **Git remote:** `github.com/0xPCP/rbc` (private)

## Dev/deploy workflow

1. Implement feature locally in `D:\Projects\rbc\`
2. Write/update test harness for the feature (see `tests/`)
3. Run tests: `pytest` inside the container or locally
4. Commit to GitHub with a message naming the feature
5. `robocopy` project to `\\192.168.50.189\docker\projects\rbc\` (excluding `.git`, `__pycache__`, `*.pyc`)
6. SSH to TrueNAS: `cd /mnt/fast/docker/projects/rbc && docker compose up -d --build`
7. If schema changed: `docker compose exec web python seed.py` (wipe + re-seed dev DB)

## Testing rules

- Every new feature must have a corresponding test module or additions to an existing one in `tests/`
- Tests that need data use the fixtures in `tests/conftest.py` — extend conftest rather than duplicating setup
- If a feature requires test data beyond what conftest provides, add it to `seed.py`
- Run the full suite before every commit: all tests must pass

## Infrastructure notes

- Traefik reverse proxy handles TLS (`*.pcp.dev` wildcard cert, entrypoint-level — do NOT add per-router `tls.certresolver` labels)
- Docker network: `internal` (external, pre-existing on TrueNAS)
- Watchtower disabled (`com.centurylinklabs.watchtower.enable=false`) — local builds only
- DB credentials live in `.env` (not committed); see `.env.example`

## Key files

| File | Purpose |
|------|---------|
| `app/__init__.py` | App factory, context processor (injects `version`, `now`) |
| `app/models.py` | SQLAlchemy models |
| `app/routes/` | Blueprints: `main`, `auth`, `rides`, `admin`, `strava` |
| `app/weather.py` | Weather fetch + WMO condition logic (Open-Meteo) |
| `app/templates/` | Jinja2 templates; `base.html` is the layout |
| `seed.py` | Dev seed data — wipe and re-run after schema changes |
| `tests/conftest.py` | Pytest fixtures (app, client, db, seeded users/rides) |
