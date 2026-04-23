# Cycling Clubs App — Task Backlog

Status: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Foundation (multi-tenant refactor)

- [ ] Add `Club` model (name, slug, description, logo, location, lat/lng, contact info)
- [ ] Add `ClubMembership` model (user ↔ club subscription/favorite)
- [ ] Add `ClubWaiver` model (waiver text, version, year) + `WaiverSignature` (user, club, year, signed_at)
- [ ] Refactor `Ride` model to belong to a `Club` (add `club_id` FK)
- [ ] Refactor admin routes to be scoped per-club (club admin role)
- [ ] Update seed data to create multiple clubs with realistic data
- [ ] Write tests for all new models and club-scoped routes

## User home screen

- [ ] Build user dashboard (`/`) — shows rides registered across all subscribed clubs
- [ ] Internal API endpoint: `GET /api/clubs/<id>/rides` (filterable by date, pace)
- [ ] "What to Wear" weather widget on dashboard using user's saved address (port from `weatherapp`)
- [ ] Write tests for dashboard and API endpoints

## Club discovery & map

- [ ] Club search by name (simple text search on club name/description)
- [ ] Club/ride search by zip code — geocode zip → lat/lng, find clubs within radius
- [ ] Interactive map page (Leaflet + OpenStreetMap) showing club pins + upcoming rides
- [ ] Write tests for search and geocoding logic

## Ride features

### Recurring rides
- [ ] Add `recurrence_rule` field to `Ride` (e.g., `WEEKLY:TUE:17:00`)
- [ ] Admin UI: checkbox "Repeat weekly" with day/time picker
- [ ] Background job or on-demand generator to create future instances
- [ ] Write tests for recurrence generation

### Weather-based auto-cancel
- [ ] Define cancellation thresholds (rain probability, wind speed, temperature) — configurable per club
- [ ] Scheduled check: morning of ride day, mark cancelled if thresholds exceeded
- [ ] Notify signed-up riders (future: email; for now, flag on ride page)
- [ ] Write tests for cancellation logic

### Add to calendar
- [ ] Generate `.ics` file per ride (RFC 5545)
- [ ] "Add to Calendar" button on ride detail page
- [ ] Write tests for `.ics` output

### Waiver gate
- [ ] Waiver acceptance flow: display waiver text, checkbox + "I agree", record signature
- [ ] Check signature before allowing ride signup; redirect if missing/expired (yearly)
- [ ] Write tests for waiver gate

## Advanced integrations (research required)

### Garmin / Wahoo
- [ ] Research Garmin Connect IQ and Wahoo APIs for route send-to-device / course export
- [ ] Implement route export button on ride page (likely `.fit` or `.gpx` download)

### Strava
- [ ] Research latest Strava Club API (v3) — what club data is publicly accessible?
- [ ] Identify useful features: activity feed, segment leaderboards, club members
- [ ] Implement chosen Strava features on club/ride pages

### Social media photo feeds
- [ ] Research Facebook Graph API for club album/page photo pull
- [ ] Research Instagram Basic Display API or hashtag approach
- [ ] Implement photo gallery section on ride detail page (post-ride recap)

## Future / icebox

- [ ] Third-party OAuth login (Google, Microsoft)
- [ ] Automated email notifications (ride reminders, cancellations, new rides from subscribed clubs)
- [ ] Club admin can invite members via email
- [ ] Mobile-responsive design audit
- [ ] Public club pages (no login required to browse rides)
