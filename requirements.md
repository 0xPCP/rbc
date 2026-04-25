# Cycling Clubs App — Requirements

## Overview

A multi-tenant web platform where any cycling club can host their presence. Users register once, subscribe to clubs, and manage all their rides from a single home screen regardless of which club is hosting them.

---

## User features

### Account & profile
- Register with email + password; profile includes name, address/zip code
- Future: third-party OAuth (Google, Microsoft)
- Future: automated email notifications

### Home screen (logged-in user)
- Shows all upcoming rides the user has registered for, across all subscribed clubs
- Rides are fed from each club's calendar via internal API
- "What to Wear" cycling weather widget based on the user's saved address
  - Self-hosted; logic ported from the `weatherapp` project (Open-Meteo, no external dependency)

### Club discovery
- Search clubs by name
- Find local clubs and rides by zip code / address
- Interactive map showing club locations and upcoming rides (Leaflet + OpenStreetMap)

### Club subscription & membership
- Join any club (public listing + map always shows all clubs)
- Two join approval modes per club: **auto-approve** (immediate active membership) or **manual** (admin must approve)
- Pending membership state: user sees "Pending Approval" badge until approved
- Unsubscribe / leave club at any time
- Club members' rides appear automatically on the user's home screen
- Club admins can approve or reject pending membership requests from the Team page

---

## Club features

### Club page
- Club name, description, logo, contact info
- Ride calendar (weekly schedule + special events)
- All clubs are discoverable on the map and Find Clubs page regardless of privacy settings
- **Private clubs**: route details (RideWithGPS embed, GPX download, route URL) are hidden from non-members
- **Membership-required clubs**: users must have an active membership to sign up for rides

### Club membership settings (admin-configurable)
- `require_membership`: toggle whether active membership is required before ride signup
- `join_approval`: `auto` (user joins immediately) or `manual` (admin approves each request)
- Team management page shows pending requests with approve/reject actions
- Pending member count badge on admin dashboard

### Club rules / waiver
- Users must accept the waiver once per calendar year before signing up for any ride at that club
- If a user has not signed, redirect to waiver acceptance flow before allowing ride registration

### Ride management (club admin)
- Create / edit / cancel rides
- Fields: title, date, time, distance, elevation, pace category, meeting location, description, route (RideWithGPS URL), video URL
- Mark a ride as recurring (e.g., every Tuesday at 6 PM) — generates future instances automatically
- Auto-cancel based on weather (configurable threshold; uses Open-Meteo forecast)
- "Add to calendar" button per ride (exports `.ics` for Outlook, Google Calendar, Apple Calendar)

### Ride page
- RideWithGPS map embed
- Signed-up riders list
- Weather forecast chip for ride date/time/location
- Garmin / Wahoo advanced features (to be researched — route send-to-device, course export)
- Strava integration (to be researched — latest Strava Club API capabilities)
- Social media photo feeds (to be researched — Facebook, Instagram album/hashtag pull)
- Ride waiver / rules acknowledgment gate (see above)

---

## API

- Internal REST endpoints so club ride feeds can be consumed by the user home screen aggregator
- Structure TBD; must support filtering by club, date range, and pace category

---

## Non-functional requirements

- All third-party services (weather, maps) must be self-hostable or use free/open APIs — no paid API keys required for core functionality
- Every feature ships with a test harness (pytest); all tests must pass before merge
- Docker on TrueNAS Scale is the dev environment; deployment is via `docker compose up -d --build`
- The platform must support multiple clubs from day one (multi-tenant data model)
