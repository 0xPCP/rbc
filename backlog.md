# Cycling Clubs App — Deferred Backlog

Features in this file require external service accounts, API keys, payment configuration,
or significant third-party integration work before they can be built. They stay here until
the relevant external dependency is ready to configure.

---

## Payments & Membership Dues (requires Stripe account)

- [ ] Membership tiers — `MembershipTier` model: name, price, description (individual, family, student, senior)
- [ ] Stripe integration for annual dues payment — collect dues on join, store `stripe_customer_id` on User
- [ ] Membership expiry date — `ClubMembership.expires_at`; grace period configurable per club
- [ ] Membership lapse: downgrade to inactive after grace period; block ride signup
- [ ] Membership renewal reminder email — 30 days and 7 days before expiry
- [ ] Automatic renewal / recurring billing (Stripe Billing)
- [ ] Treasurer admin role — view financial reports and export member/payment data
- [ ] Treasurer dashboard: dues collected YTD, outstanding renewals
- [ ] CSV financial export: payment history per member
- [ ] Event registration payment (separate from membership dues)
- [ ] Early bird / tiered event pricing; promo codes

**Needs:** Stripe publishable + secret key, webhook endpoint, test mode setup

---

## OAuth Login (requires Google / Microsoft app registration)

- [ ] Google OAuth login — register app in Google Cloud Console, configure client ID + secret
- [ ] Microsoft OAuth login — register app in Azure AD
- [ ] Flask-Dance or Authlib integration

**Needs:** OAuth app registration at Google Cloud Console and/or Azure AD

---

## Social Media Photo Feeds (requires API access)

- [ ] Facebook Graph API — club album/page photo pull (requires app review for public pages)
- [ ] Instagram Basic Display API or hashtag approach (requires Meta app review)
- [ ] Photo gallery section on ride detail page (post-ride recap)

**Needs:** Meta developer account, app review approval for public data access

---

## Device Route Push (requires RideWithGPS / Garmin API credentials)

- [ ] Direct route send to Garmin Connect (via Garmin Health API or Connect IQ)
- [ ] Direct route send to Wahoo (via Wahoo Cloud API)
- [ ] RideWithGPS API key for server-side route operations

**Needs:** Garmin developer account, Wahoo developer account, RideWithGPS API key

---

## Real-Time Ride Tracking (requires location infrastructure)

- [ ] Opt-in group location sharing during rides (safety use case)
- [ ] Research: WebSockets vs. polling; privacy model; data retention policy

**Needs:** Architecture decision, WebSocket infrastructure, privacy/legal review

---

## Custom Domains (requires DNS / Cloudflare configuration)

- [ ] Map `clubname.com` to club's platform page (Cloudflare Worker / CNAME proxy)

**Needs:** Cloudflare Worker setup, SSL certificate strategy per custom domain

---

## Annual Events with Registration (significant scope)

- [ ] Event pages distinct from weekly rides — centuries, gran fondos, crits, clinics
- [ ] Multiple route options per event (25 / 50 / 75 / 100 mi)
- [ ] Volunteer sign-up for SAG, rest stops, finish line
- [ ] Post-event results / finisher list

**Depends on:** Stripe payments (above) for registration fees

---

## Timing Integration (requires timing vendor API)

- [ ] Timed event integration — RaceJoy, ChronoTrack, or similar
- [ ] Real-time results feed

**Needs:** Timing vendor API access + agreement
