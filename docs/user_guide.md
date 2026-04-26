# User Guide — Cycling Clubs Platform

This guide covers everything you need to know as a rider or club administrator. It is split into two parts:

- **Part 1 — Riders**: finding clubs, joining rides, managing your profile
- **Part 2 — Club Admins**: creating and running a club, managing members and rides

---

# Part 1: Riders

## Creating an account

Go to the platform URL and click **Register**. You need:

- A username (3–50 characters)
- An email address (used for login and notifications)
- A password (minimum 8 characters)

Once registered you are taken to your home dashboard.

---

## Your home dashboard

After logging in you land on your personal dashboard. It shows:

- **My upcoming rides** — all rides you are signed up for, across every club you've joined
- **What to Wear** — a weather widget for your saved zip code with conditions and gear recommendations
- **Suggested rides** — upcoming rides from your clubs that you haven't signed up for yet
- **Clubs near you** — clubs in your area based on your zip code

---

## Finding clubs

Click **Find Clubs** in the navigation. You can:

- **Search by name** — type any part of a club's name or description
- **Search by zip code** — enter a zip and a radius (default 50 miles) to find clubs near you
- **Browse the map** — click **Map** to see all clubs on an interactive map

Click any club name to visit its home page.

---

## Joining a club

On a club's home page, click **Join Club**.

- If the club has **open enrollment**, you become a member immediately.
- If the club requires **admin approval**, your request is submitted and marked as pending. You'll receive an email once an admin approves or declines your request.

Once you're a member you can sign up for rides and access any member-only content.

---

## Signing the annual waiver

Most clubs require you to sign a waiver once per year before you can sign up for rides. When you try to sign up for your first ride of the year, you will be taken to the waiver page automatically.

Read the waiver text, check the "I agree" box, and click **Sign Waiver**. You won't be asked again for the rest of the year.

---

## Signing up for a ride

Open a club's **Rides** page to see the upcoming calendar. Click any ride to open its detail page. If the ride is open and you meet the requirements, click **Sign Up**.

Things that can prevent signup:
- You are not yet an active member (if the club requires membership)
- You haven't signed this year's waiver
- The ride is full — in that case you'll be added to the **waitlist** automatically

If you're on the waitlist and a spot opens up (someone cancels), you'll be moved up automatically and notified by email.

---

## Cancelling a signup

On the ride detail page, click **Cancel My Signup**. If you cancel and were on the roster (not the waitlist), the next person on the waitlist is promoted automatically.

---

## Ride calendar views

Club ride calendars have three views:

- **List** — all upcoming rides as a scrollable list, grouped by month. Days with multiple rides (e.g., A, B, and C groups on the same day) are shown as a collapsed card — click to expand.
- **Week** — a 7-day view showing the current week
- **Month** — a full calendar month grid

Use the **Pace** filter (A / B / C / D) and **Type** filter (Road, Gravel, Social, etc.) to narrow the list.

---

## Adding a ride to your calendar

On any ride detail page, click **Add to Calendar** to download an `.ics` file. This works with Google Calendar, Apple Calendar, Outlook, and any other app that supports the iCalendar format.

---

## Downloading a route

If a ride has a route attached, a **Download GPX** button will appear on the ride detail page. The GPX file can be loaded onto Garmin, Wahoo, Hammerhead, and most other GPS computers.

---

## Ride comments

You can ask questions or post updates on any ride detail page. The comment section is visible to all members.

- Type your message in the box and click **Post**.
- You can delete your own comments at any time.

---

## Sharing photos and videos after a ride

After a ride has taken place (the ride date has passed), a **Media** section appears at the bottom of the ride detail page.

**Photos**: click **Share a Photo**, choose an image (JPEG, PNG, or WebP, max 5 MB), add an optional caption, and upload. Photos are automatically resized to a standard web size. You can upload up to 5 photos per ride.

**Videos**: paste a YouTube, Strava, or Vimeo link and click **Share Video**. The video will be embedded on the page.

Photos are automatically removed 90 days after the ride date.

---

## Your profile

Click your username in the navigation and choose **Profile**.

You can update:

- **Username and email**
- **Zip code** — used for the weather widget and finding nearby clubs
- **Emergency contact** — name and phone number. This is optional and only visible to ride leaders and club admins on the roster for a ride you're signed up for.
- **Gear inventory** — check off the gear you own. The weather widget uses this to give you personalised recommendations (e.g., "bring your rain jacket" or "arm warmers recommended").

Your profile also shows your **ride history** — total rides completed, miles, and elevation year-to-date across all your clubs.

---

## Linking Strava

On your profile page, click **Connect Strava** to link your Strava account. This enables Strava-powered features for clubs that have the integration enabled.

---

## Ride history

Your profile page shows a summary of rides you've attended across all clubs, including total miles and elevation for the current year. Individual clubs may also show a leaderboard of most active riders.

---

## Leaving a club

On the club's home page, click **Leave Club**. You will be removed as a member. Any future ride signups you have at that club are not automatically cancelled — you should cancel those first if you want to free up spots for other riders.

---

---

# Part 2: Club Administrators

## Roles overview

The platform has four admin roles. A user can hold only one role per club.

| Role | What they can do |
|---|---|
| **Admin** | Everything — settings, members, rides, content, financial data |
| **Ride Manager** | Create and edit rides, view rosters, record attendance |
| **Content Editor** | Write and edit news posts and the club description |
| **Treasurer** | View and export the member list |

Club admins are separate from regular members. A user can be both a member and an admin of the same club.

---

## Creating a club

Click **Create a Club** (available after logging in). The wizard walks you through five steps:

1. **Basic info** — club name, city, state, zip code
2. **Privacy** — whether the club is public or private (see below)
3. **Theme** — choose one of 6 preset color schemes or pick your own colors with a live preview
4. **Media** — logo URL and banner image URL
5. **Review** — confirm and create

You are automatically made the first admin and an active member of your new club.

---

## Public vs. private clubs

**Public clubs** are fully open. Anyone can see ride details, route files, and comments.

**Private clubs** hide route URLs, GPX files, the RideWithGPS map embed, photos, and comments from anyone who is not an active member. The club itself still appears in search results and on the map — only the detailed content is gated.

Set privacy in **Admin → Settings → Privacy & Membership**.

---

## Club settings

Go to **Admin → Settings** to configure:

- **Basic info**: name, description, city/state/zip, contact email, logo URL, banner URL
- **Theme**: primary and accent colors with live preview
- **Privacy & Membership**:
  - *Private club* toggle — hides content from non-members
  - *Require membership* — riders must be active members to sign up for rides
  - *Join approval* — Auto (instant) or Manual (admin approves each request)
- **Strava**: enter your club's Strava club ID to show a recent activity feed on the club home page
- **Weather auto-cancel**: enable and set thresholds for rain probability (%), wind speed (mph), and temperature range (°F). The system checks each morning and cancels rides automatically if conditions breach your thresholds, then emails all signed-up riders.

---

## Managing your admin team

Go to **Admin → Team**.

**To add a team member**: enter their username or email address, choose a role, and click **Add**.

**To change a role**: remove the user and add them again with the new role.

**To remove a team member**: click **Remove** next to their name. You cannot remove the last remaining admin — there must always be at least one admin.

---

## Managing members

The **Team** page also shows your full member list and any pending membership requests.

**Approving / rejecting requests**: When *join approval* is set to Manual, new join requests appear under **Pending Approval**. Click **Approve** to grant active membership (the user is notified by email) or **Reject** to decline (the user is also notified).

**Adding a member directly**: Scroll to **Add Member**, enter their email or username, and click **Add**. This bypasses approval and sets them as active immediately.

**Removing a member**: Click **Remove** next to any member's name.

**Exporting the member list**: Click **Export CSV** to download a spreadsheet with each member's name, email, join date, status, and emergency contact details.

---

## Inviting someone by email

Go to **Admin → Invites**. Enter the person's email address and click **Send Invite**.

They will receive an email with a link. When they click it (and log in or register if needed), they are automatically given active membership — no approval step required, even if your club uses manual approval.

Invite links expire after 7 days. You can see the status of recent invites on the same page.

---

## Creating a ride

Go to **Admin → Rides → New Ride**.

Fill in:

- **Title** — e.g., "Tuesday A Ride"
- **Date and time**
- **Meeting location**
- **Distance (miles)** and optional **elevation (feet)**
- **Pace category** — A (22+ mph), B (18–22 mph), C (14–18 mph), D (<14 mph)
- **Ride type** — Road, Gravel, Social, Training, Event, or Night
- **Ride leader** — choose from the member roster or type a name manually
- **Route URL** — paste a RideWithGPS URL to auto-embed the map and enable GPX download
- **Video URL** — paste a YouTube or Vimeo link to embed in the ride detail
- **Description** — any additional notes
- **Max riders** — leave blank for unlimited; set a number to enable automatic waitlisting
- **Repeat weekly** — check to generate 8 weekly copies of this ride automatically

Click **Create Ride**. All active members receive a notification email.

---

## Recurring rides

When you check **Repeat weekly**, the platform creates 8 individual ride instances automatically (one per week for the next 8 weeks from the date you enter). Each instance is an independent ride.

If you edit the original (template) ride and change the date, location, or other details, the future instances are deleted and regenerated with the new information.

To stop a recurring series, delete the template ride or uncheck **Repeat weekly** and save.

---

## Editing and cancelling rides

Go to **Admin → Rides**, find the ride, and click **Edit**.

To cancel a ride without deleting it, check the **Cancelled** box and save. All signed-up riders receive a cancellation email. The ride remains visible on the calendar as cancelled.

To delete a ride permanently, click **Delete** on the ride edit page or ride list.

---

## Weather auto-cancel

If you enable weather auto-cancel in settings, the system runs each morning and checks the forecast for your club's location. If any of your thresholds are exceeded:

- The ride is marked as cancelled
- A cancellation email is sent to all signed-up riders with the weather reason stated

You can adjust the thresholds at any time in **Admin → Settings → Weather Auto-Cancel**. Default thresholds:

- Rain probability: 70%
- Wind speed: 30 mph
- Temperature minimum: 20°F
- Temperature maximum: 100°F

Set to 0 / very large numbers to effectively disable individual checks while keeping auto-cancel on.

---

## Viewing the ride roster

Go to **Admin → Rides**, find a ride, and click **Roster**. You'll see:

- **Signed up** — confirmed riders, with email and emergency contact details
- **Waitlist** — riders waiting for a spot, in order of signup

Emergency contact details (name and phone number) are only visible here — they are not shown on any public page.

---

## Recording attendance

After a ride has taken place, open the roster and a checkbox column appears next to each rider. Check the box for everyone who showed up, then click **Save Attendance**. Rows highlight green (attended) or red (no-show).

Attendance data feeds into member ride history and, in future, club leaderboards.

---

## News and announcements

Go to **Admin → Posts → New Post**. Enter a title and body text, then click **Publish**. Posts appear on the club home page in reverse-chronological order.

Content editors (if you've assigned that role to someone) can create and edit posts without having full admin access.

---

## Ride leader roster

Go to **Admin → Leaders** to manage the public ride leader roster shown on your club's public page.

For each leader you can add:
- **Name** and **bio**
- **Photo URL**
- **Display order** (lower number = shown first)

---

## Sponsors

Go to **Admin → Sponsors** to add sponsor logos to your club home page. For each sponsor:

- **Name**
- **Logo URL**
- **Website URL** (the logo links to this)
- **Display order**

---

## Club stats

Your club home page automatically shows:

- **Founded** — year of first ride or club creation
- **Members** — current active member count
- **Rides hosted** — all-time total ride count
- **Total miles** — combined distance of all rides ever posted

These update automatically as you add rides and members.

---

## Waivers

If your club requires a waiver, go to **Admin → Settings** (waiver section is accessible for admins). Create a waiver with a title and body text for the current year. Riders will be required to sign it before they can register for any ride.

Waivers are year-specific. At the start of each new year, riders will be prompted to sign again automatically.

---

## Tips for new club admins

**Start with settings.** Set your theme colors, description, and contact email before inviting anyone — it makes a better first impression.

**Use Manual approval at first.** While you're getting started, setting join approval to Manual gives you control over who joins. Switch to Auto once you're comfortable.

**Create your ride template once, repeat weekly.** For a club with a regular weekly ride structure (e.g., Tuesday A, Wednesday B, Thursday C), create each ride once with Repeat Weekly checked. This populates 8 weeks of the calendar in one go.

**Set weather thresholds conservatively.** Auto-cancel is a convenience, not a replacement for your own judgement. Review cancelled rides in case conditions improve — you can un-cancel a ride by unchecking the Cancelled box and saving.

**Keep the ride leader roster up to date.** Riders appreciate knowing who is leading a ride. Use the Leaders page to keep photos and bios current.

**Use invites for your founding members.** The invite link is the easiest way to bring in your core group — they click a link, sign up (or log in), and are immediately active members with no approval step.
