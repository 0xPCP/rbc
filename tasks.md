# Cycling Clubs App — Task Backlog

Status: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Foundation (multi-tenant refactor)

- [x] Add `Club` model (name, slug, description, logo, location, lat/lng, contact info)
- [x] Add `ClubMembership` model (user ↔ club subscription/favorite)
- [x] Add `ClubWaiver` model (waiver text, version, year) + `WaiverSignature` (user, club, year, signed_at)
- [x] Refactor `Ride` model to belong to a `Club` (add `club_id` FK)
- [x] Refactor admin routes to be scoped per-club (club admin role)
- [x] Update seed data to create multiple clubs with realistic data
- [x] Write tests for all new models and club-scoped routes

## User home screen

- [x] Build user dashboard (`/`) — shows rides registered across all subscribed clubs
- [x] Internal API endpoint: `GET /api/clubs/map-data` (club pins for Leaflet map)
- [x] "What to Wear" weather widget on dashboard using user's saved address
- [x] Write tests for dashboard and API endpoints

## Club discovery & map

- [x] Club search by name (simple text search on club name/description)
- [x] Club/ride search by zip code — geocode zip → lat/lng, find clubs within radius
- [x] Interactive map page (Leaflet + OpenStreetMap) showing club pins + upcoming rides
- [x] Write tests for search and geocoding logic

## Ride features

### Recurring rides
- [x] Add `recurrence_rule` field to `Ride`
- [x] Admin UI: checkbox "Repeat weekly" with instance generator
- [x] On-demand generator to create 8 weeks of future instances
- [x] Write tests for recurrence generation

### Weather-based auto-cancel
- [x] Define cancellation thresholds (rain probability, wind speed, temperature) — configurable per club
- [x] Scheduled check: morning of ride day (APScheduler, 6 AM), mark cancelled if thresholds exceeded
- [x] Flag cancel reason on ride page; email notifications (see below)
- [x] Write tests for cancellation logic

### Add to calendar
- [x] Generate `.ics` file per ride (RFC 5545)
- [x] "Add to Calendar" button on ride detail page
- [x] Write tests for `.ics` output

### Waiver gate
- [x] Waiver acceptance flow: display waiver text, checkbox + "I agree", record signature
- [x] Check signature before allowing ride signup; redirect if missing/expired (yearly)
- [x] Write tests for waiver gate

### GPX / route export
- [ ] Proxy GPX download from RideWithGPS for rides with a route URL
- [ ] "Download GPX" button on ride detail page (works with Garmin, Wahoo, Hammerhead)
- [ ] Write tests for GPX proxy

## Email notifications
- [x] Flask-Mail integration (SMTP config via env vars)
- [x] Cancellation email to all signed-up riders when a ride is cancelled
- [x] Ride reminder email to signed-up riders (via scheduler, morning of ride)
- [x] New ride notification to club members when admin creates a ride
- [x] Write tests (mock SMTP)

## Club theming
- [x] Per-club primary color + derived CSS variable palette (dark/light/pale variants)
- [x] Per-club accent/button color
- [x] Logo URL + banner image on club home page header (with gradient overlay)
- [x] Admin settings UI: color pickers + live preview card
- [x] Write tests for color utilities, template injection, admin form

## Advanced integrations (research required)

### Strava
- [x] Member OAuth (connect/disconnect Strava account from profile)
- [x] Club activity feed (recent activities via club refresh token)
- [ ] Surface Strava activity feed on club page (currently fetched, not displayed)

### Social media photo feeds
- [ ] Research Facebook Graph API for club album/page photo pull
- [ ] Research Instagram Basic Display API or hashtag approach
- [ ] Implement photo gallery section on ride detail page (post-ride recap)

## Future / icebox

- [ ] Third-party OAuth login (Google, Microsoft)
- [ ] Club admin can invite members via email
- [ ] Mobile-responsive design audit
- [ ] Public club pages — already accessible without login; audit completeness
