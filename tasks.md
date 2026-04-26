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

## Club creation & permissions (v0.010)

- [x] Club creation wizard (`/clubs/create`) — 5-step: basic info, privacy, theme, media, review
- [x] 6 preset themes + custom color picker with live preview
- [x] `ClubAdmin.role`: `'admin'` (full) | `'ride_manager'` (rides only)
- [x] Team management page — add/remove admin team members, manage members
- [x] Club dashboard shows full-admin-only buttons (Team, Settings) conditionally

## Membership system (v0.011)

- [x] `Club.require_membership`: gate ride signups behind active club membership
- [x] `Club.join_approval`: `'auto'` (join immediately) | `'manual'` (admin approves)
- [x] `ClubMembership.status`: `'active'` | `'pending'`
- [x] `User.is_active_member_of()` and `is_pending_member_of()` helpers
- [x] `join()` route respects club approval mode
- [x] `ride_signup()` blocks non-active-members when `require_membership=True`
- [x] Private clubs hide route URL, RideWithGPS embed, and GPX from non-members
- [x] `ride_gpx()` returns 403 for non-members on private clubs
- [x] Club home shows "Pending Approval" state for pending members
- [x] Admin team page shows pending requests with approve/reject actions
- [x] Admin dashboard shows pending member count badge
- [x] Club settings: Membership section with `require_membership` toggle + `join_approval` dropdown
- [x] seed.py: `test@pcp.dev` / `password` added as RBC admin; NVCC set to manual-approval private club
- [x] 25 new tests in `test_membership.py`

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
- [x] Proxy GPX download from RideWithGPS for rides with a route URL
- [x] "Download GPX" button on ride detail page (works with Garmin, Wahoo, Hammerhead)
- [x] Write tests for GPX proxy

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
- [x] Surface Strava activity feed on club page (per-club strava_club_id, cached feed)

### Social media photo feeds
- Moved to `backlog.md` — requires Meta app review for API access

---

## Backlog — High Priority

These are the features most commonly found across major clubs (NYCC, Cascade, BTCNJ, DC Velo, etc.)
and platforms (ClubExpress, RideStats, RideWithGPS for Clubs).

### Notifications
- [x] Weekly ride digest email — automated Sunday preview of upcoming club rides for each member
- [x] Membership approval/rejection email — notify user when request is approved or rejected
- [ ] Membership renewal reminder email — moved to backlog.md (depends on Stripe expiry)
- [x] Write tests for new notification types (covered by existing email mock tests)

### Ride enhancements
- [x] Ride cap (max riders) + waiting list — `Ride.max_riders`, waitlist auto-promotes when slot opens
- [x] Ride tags / type: road, gravel, social, training, event, night ride (filter on calendar + discovery)
- [x] Add tag filter to club calendar (alongside existing pace filter)
- [x] Add `is_private` toggle to club settings UI (model field exists; settings page needs UI)

### Membership & dues
- Moved to `backlog.md` — requires Stripe account configuration

### Admin tooling
- [x] CSV export — member list (name, email, join date, status) downloadable by admin
- [x] Emergency contact on member profile — name + phone; visible to ride leaders on ride day
- [x] Ride leader assignment from member roster (stored on `Ride.leader_id`)
- [x] Write tests for CSV export and emergency contact visibility

---

## Backlog — Medium Priority

### Club page & content
- [x] Club news / announcements — admin-authored posts with title, body, published date; listed on club home
- [x] Club stats block on public page: founded year, member count, total rides hosted, total miles
- [x] Ride leader roster (public): name, bio, photo per leader
- [x] Sponsor / partner logos section on club home page
- [x] Write tests for news CRUD and stats rendering

### User profile & history
- [x] Emergency contact field on user profile (name + phone) — opt-in; visible to ride leaders
- [x] Ride history page — "You've completed 47 rides this year across 3 clubs"
- [x] Personal stats: miles and elevation YTD across all joined clubs
- [x] Write tests for history aggregation

### Ride discovery (cross-club)
- [x] "All rides near my zip this weekend" — discovery page showing rides from all clubs near zip
- [x] Filter by pace category, distance, date across all clubs
- [x] Write tests for cross-club ride discovery query

### Roles expansion
- [x] `content_editor` role — can manage news posts and club description only (no rides or settings)
- [x] `treasurer` role — can view/export financial data; cannot edit settings or rides
- [x] Write tests for new role access control

### Invite-by-email
- [x] Admin sends invite link (time-limited token); recipient gets immediate active membership on click
- [x] Write tests for invite token generation, redemption, and expiry

---

## Backlog — Lower Priority / Icebox

### Annual events
- [ ] Event pages distinct from weekly rides — centuries, gran fondos, crits, clinics
- [ ] Event registration with optional Stripe payment
- [ ] Multiple route options per event (25 / 50 / 75 / 100 mi)
- [ ] Volunteer sign-up for SAG, rest stops, finish line
- [ ] Early bird / tiered pricing; promo codes

### Member engagement
- [x] Attendance history for ride leaders — `RideSignup.attended` bool; roster checkboxes after ride date; admin POST `/attendance` route
- [ ] "Most rides" / "Most miles" club awards (annual)

### Safety
- [ ] QR code check-in at rides — admin generates per-ride QR; scan records attendance
- [ ] Ride leader first-aid cert field + expiry tracking (admin visible)
- [ ] Per-event waivers — separate waiver for special events (night rides, crits, gravel)
- [ ] Minor / youth waiver requiring parent signature (email link flow)

### Platform
- [x] Platform-level superadmin dashboard — all clubs, all stats, per-club upcoming count, status badges
- [ ] Webhook: notify external systems on ride create/cancel/update
- [ ] Custom domain: map clubname.com to their platform page (Cloudflare Worker / CNAME)

### OAuth & social
- OAuth login moved to `backlog.md` — requires Google/Microsoft app registration
- [x] Post-ride media sharing — photos (upload, resize, expiry) + video links (YouTube/Strava/Vimeo embeds); ride detail page shows a media feed after ride date; strategy documented in `docs/media_strategy.md`
- Real-time ride tracking moved to `backlog.md` — requires architecture + privacy review

### UX polish
- [x] Mobile-responsive design audit — ride-card CSS defined, mobile breakpoint fixes applied
- [x] Multi-group ride card — A + B + C groups on same day shown as one collapsible card (Bootstrap collapse)
- [x] Ride comment thread — members ask questions, post updates before/after ride
- [ ] Direct route send to Garmin / Wahoo (via RideWithGPS API or device API)
