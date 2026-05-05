# Post-Ride Media Sharing — Strategy & Constraints

## Why this document exists

Media storage is the one feature that can generate unbounded cost if left unconstrained.
This document records every decision and its rationale so future changes are deliberate,
not accidental drift.

---

## Core decisions

### Videos: external links only, no server storage

Users upload video to YouTube, Strava, or Vimeo and paste the link.
The app stores the URL and embeds it via iframe (same mechanism as ride route videos).

**Why:** A single Insta360 clip is 4–8 GB. Even phone video is 500 MB+.
Transcoding for cross-browser compatibility requires CPU time or a paid service
(Cloudflare Stream, Mux, etc.). At current scale these costs are not justified.

**To change this:** Evaluate Cloudflare Stream ($1/1000 min stored, $1/1000 min delivered)
or Mux when clubs are large enough that video upload is a real friction point.
Update `UPLOAD_FOLDER` handling in `app/routes/media.py` and add a transcoding step.

### Photos: direct upload, resized on ingest, local storage for dev

JPEG/PNG/WebP only. Input capped at 5 MB (Flask `MAX_CONTENT_LENGTH`).
Pillow resizes to max 1200 px wide and re-saves as JPEG quality 85 before storing.
Files land in `uploads/ride_media/<ride_id>/<uuid>.jpg` on the host filesystem.

**Why for current TrueNAS/dev:** Phone photos are the primary use case. After resize, a typical photo is 150–300 KB.
At 30 photos/ride × 300 KB × 500 rides/year ≈ 4.5 GB/year — manageable on a NAS dataset.

**Production direction:** The planned production deployment uses DigitalOcean App Platform,
Managed PostgreSQL, and DigitalOcean Spaces. App Platform containers are disposable, so
uploaded media must move to Spaces before production cutover. See
`docs/digitalocean_deployment.md`.

**To change storage backend to DigitalOcean Spaces:**
1. Add `boto3` (Spaces is S3-compatible) and Spaces credentials to environment variables.
2. Replace `_save_photo()` in `app/routes/media.py` with an S3 `put_object` call.
3. Replace `serve_photo` route with a signed-URL redirect or a public Spaces/CDN URL.
4. Update `purge_expired_media` in `app/scheduler.py` to call `delete_object` instead of `os.remove`.
5. The model and limits are unchanged.

### Post-ride gate

The upload forms are only shown (and the routes only accept uploads) when
`ride.date <= today`. Prevents pre-ride clutter; photos are inherently post-event.

### Access control

Photos on private clubs are served through Flask (`/media/ride/<id>/<filename>`)
which checks active membership before sending the file. Public club photos are served
directly with no auth check.

---

## Configurable limits

All limits are environment variables with sensible defaults.
Edit `.env` to adjust without a code deploy.

| Variable | Default | Meaning |
|---|---|---|
| `MEDIA_EXPIRY_DAYS` | 90 | Days after ride date before photos are auto-deleted |
| `MEDIA_MAX_PHOTOS_PER_USER_RIDE` | 5 | Max photos one user can upload per ride |
| `MEDIA_MAX_PHOTOS_PER_RIDE` | 30 | Total photo cap per ride across all users |
| `MEDIA_MAX_WIDTH_PX` | 1200 | Pillow resize target width (px) |
| `UPLOAD_FOLDER` | `uploads/` next to project root | Filesystem path for photo storage |
| `MAX_CONTENT_LENGTH` | 5 MB | Flask hard limit — request rejected before Pillow sees it |

---

## Auto-expiry

`purge_expired_media()` in `app/scheduler.py` runs nightly at 02:30.
It queries `RideMedia JOIN Ride WHERE ride.date < today - MEDIA_EXPIRY_DAYS`,
deletes the files from disk, and removes the DB rows.

**To extend retention:** increase `MEDIA_EXPIRY_DAYS` in `.env`. Existing files are
unaffected until the new cutoff catches them.

**To disable expiry entirely:** set `MEDIA_EXPIRY_DAYS=99999`.

---

## Storage estimate

| Scenario | Est. storage/year |
|---|---|
| 100 rides, 10 photos/ride, 250 KB avg | ~250 MB |
| 500 rides, 20 photos/ride, 300 KB avg | ~3 GB |
| 1000 rides, 30 photos/ride, 300 KB avg | ~9 GB |

At 90-day expiry, steady-state storage is roughly (rides/year ÷ 4) × avg photo count × avg size.

---

## Deployment checklist

- Mount `uploads/` as a persistent Docker volume (not inside the container image).
- Add `uploads/` to `.gitignore` (already done).
- On TrueNAS: map the volume to a dataset on `fast` pool, e.g. `/mnt/fast/docker/projects/rbc/uploads`.
- Compose entry: `- /mnt/fast/docker/projects/rbc/uploads:/app/uploads`
