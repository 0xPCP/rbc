(function () {
  'use strict';

  const RBC_GREEN  = '#2d6a4f';
  const RBC_ORANGE = '#e76f51';
  const RIDE_BLUE  = '#1a6cbf';
  const RIDE_DARK  = '#0f4c91';

  const mapEl = document.getElementById('map');
  const clubs = JSON.parse(mapEl.dataset.clubs || '[]');
  const rides = JSON.parse(mapEl.dataset.rides  || '[]');

  const map = L.map('map', { zoomControl: true }).setView([39.5, -98.35], 4);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // ── Icons ─────────────────────────────────────────────────────────────────────

  function clubIcon(isMember) {
    const fill   = isMember ? RBC_GREEN : RBC_ORANGE;
    const stroke = isMember ? '#1b4332' : '#c75c40';
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 9.63 12.5 21.4 13.03 21.9a1.38 1.38 0 0 0 1.94 0C15.5 35.4 28 23.63 28 14 28 6.27 21.73 0 14 0z"
            fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
      <circle cx="14" cy="14" r="5.5" fill="white" opacity="0.9"/>
    </svg>`;
    return L.divIcon({ className: '', html: svg, iconSize: [28,36], iconAnchor: [14,36], popupAnchor: [0,-34] });
  }

  function rideIcon() {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="34" viewBox="0 0 26 34">
      <path d="M13 0C5.82 0 0 5.82 0 13c0 8.94 11.6 19.86 12.09 20.33a1.28 1.28 0 0 0 1.82 0C14.4 32.86 26 21.94 26 13 26 5.82 20.18 0 13 0z"
            fill="${RIDE_BLUE}" stroke="${RIDE_DARK}" stroke-width="1.5"/>
      <text x="13" y="17.5" text-anchor="middle" font-size="11" fill="white" font-family="sans-serif" font-weight="bold">&#x1F6B4;</text>
    </svg>`;
    return L.divIcon({ className: '', html: svg, iconSize: [26,34], iconAnchor: [13,34], popupAnchor: [0,-32] });
  }

  // ── Popup builders ────────────────────────────────────────────────────────────

  function buildClubPopup(club) {
    const loc = club.city
      ? `<div class="club-popup-location">${club.city}${club.state ? ', ' + club.state : ''}</div>`
      : '';
    const tag = club.is_member
      ? `<span class="club-popup-member-tag">&#x2713; Member</span>`
      : '<span></span>';
    return `<div class="club-popup-body">
      <div class="club-popup-name">${club.name}</div>${loc}
      <div class="club-popup-stats">
        <span class="club-popup-stat">&#x1F6B4; ${club.members} member${club.members !== 1 ? 's' : ''}</span>
        <span class="club-popup-stat">&#x1F4C5; ${club.upcoming} upcoming</span>
      </div>
    </div>
    <div class="club-popup-footer">${tag}
      <a href="${club.url}" class="club-popup-link">View Club &rarr;</a>
    </div>`;
  }

  const PACE_LABELS = { A: 'A — Fast', B: 'B — Moderate', C: 'C — Casual', D: 'D — Beginner' };
  const TYPE_LABELS = { road: 'Road', gravel: 'Gravel', social: 'Social', training: 'Training', event: 'Event', night: 'Night Ride' };

  function fmtDate(iso) {
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }
  function fmtTime(t) {
    if (!t) return '';
    const [h, m] = t.split(':').map(Number);
    const p = h >= 12 ? 'PM' : 'AM';
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${p}`;
  }

  function buildRidePopup(ride) {
    const when = fmtDate(ride.date) + (ride.time ? ' &bull; ' + fmtTime(ride.time) : '');
    return `<div class="ride-popup-body">
      <div class="ride-popup-title">${ride.title}</div>
      <div class="ride-popup-club">&#x1F3E2; ${ride.club_name}</div>
      <div class="ride-popup-when">&#x1F4C5; ${when}</div>
      <div class="ride-popup-tags">
        <span class="ride-popup-tag tag-pace">${PACE_LABELS[ride.pace] || ride.pace} Pace</span>
        <span class="ride-popup-tag tag-type">${TYPE_LABELS[ride.ride_type] || ride.ride_type}</span>
        <span class="ride-popup-tag tag-dist">&#x1F4CF; ${ride.distance} mi</span>
      </div>
    </div>
    <div class="ride-popup-footer">
      <a href="${ride.url}" class="ride-popup-link">View Ride &rarr;</a>
    </div>`;
  }

  // ── Layer groups ──────────────────────────────────────────────────────────────

  const clubLayer = L.layerGroup().addTo(map);
  const rideLayer = L.layerGroup();

  clubs.forEach(c => {
    L.marker([c.lat, c.lng], { icon: clubIcon(c.is_member) })
      .addTo(clubLayer)
      .bindPopup(buildClubPopup(c), { maxWidth: 300, minWidth: 240 });
  });

  rides.forEach(r => {
    L.marker([r.lat, r.lng], { icon: rideIcon() })
      .addTo(rideLayer)
      .bindPopup(buildRidePopup(r), { maxWidth: 300, minWidth: 240 });
  });

  // ── Subtitle + initial fit ────────────────────────────────────────────────────

  const subtitle = document.getElementById('map-subtitle');
  let currentLayer = 'clubs';

  function updateSubtitle() {
    if (currentLayer === 'clubs') {
      subtitle.textContent = clubs.length === 0
        ? 'No geocoded clubs yet.'
        : `${clubs.length} club${clubs.length !== 1 ? 's' : ''} on the map`;
    } else {
      subtitle.textContent = rides.length === 0
        ? 'No club rides found in the next 7 days.'
        : `${rides.length} ride${rides.length !== 1 ? 's' : ''} in the next 7 days`;
    }
  }

  function fitLayer(layer) {
    const markers = [];
    layer.eachLayer(m => { if (m.getLatLng) markers.push(m.getLatLng()); });
    if (markers.length > 0) map.fitBounds(L.latLngBounds(markers), { padding: [48, 48], maxZoom: 11 });
  }

  if (clubs.length > 0) fitLayer(clubLayer);
  updateSubtitle();

  // ── Toggle handler ────────────────────────────────────────────────────────────

  function showLayer(which) {
    currentLayer = which;
    if (which === 'clubs') {
      map.addLayer(clubLayer);
      map.removeLayer(rideLayer);
      document.getElementById('layer-clubs').classList.add('active');
      const ridesBtn = document.getElementById('layer-rides');
      if (ridesBtn) ridesBtn.classList.remove('active');
    } else {
      map.removeLayer(clubLayer);
      map.addLayer(rideLayer);
      document.getElementById('layer-clubs').classList.remove('active');
      const ridesBtn = document.getElementById('layer-rides');
      if (ridesBtn) ridesBtn.classList.add('active');
      if (rides.length > 0) fitLayer(rideLayer);
    }
    updateSubtitle();
  }

  document.getElementById('layer-clubs').addEventListener('click', function () { showLayer('clubs'); });
  const ridesToggle = document.getElementById('layer-rides');
  if (ridesToggle) ridesToggle.addEventListener('click', function () { showLayer('rides'); });

  // ── Near Me ───────────────────────────────────────────────────────────────────

  document.getElementById('locate-btn').addEventListener('click', function () {
    const btn = this;
    btn.disabled = true;
    btn.textContent = 'Locating…';
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      btn.disabled = false;
      btn.innerHTML = '&#x1F4CD; Near Me';
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        map.setView([pos.coords.latitude, pos.coords.longitude], 10);
        btn.disabled = false;
        btn.innerHTML = '&#x1F4CD; Near Me';
      },
      () => {
        alert('Unable to retrieve your location.');
        btn.disabled = false;
        btn.innerHTML = '&#x1F4CD; Near Me';
      }
    );
  });
}());
