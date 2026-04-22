"""
RBC development seed data.
Run inside the container: python seed.py
Based on the real Reston Bicycle Club schedule at restonbikeclub.org
"""
from datetime import date, time
from app import create_app
from app.extensions import db, bcrypt
from app.models import User, Ride, RideSignup

app = create_app()

with app.app_context():

    # ── Users ────────────────────────────────────────────────────────────────
    pw = bcrypt.generate_password_hash('password123').decode()

    admin   = User(username='admin',    email='admin@rbc.dev',                password_hash=pw, is_admin=True)
    phil    = User(username='phil',     email='phil@pcp.dev',                 password_hash=pw)
    john    = User(username='jsmith',   email='john.smith@example.com',       password_hash=pw)
    mary    = User(username='mbaker',   email='mary.baker@example.com',       password_hash=pw)
    tom     = User(username='twheels',  email='tom.wheels@example.com',       password_hash=pw)
    kate    = User(username='kroller',  email='kate.roller@example.com',      password_hash=pw)
    dave    = User(username='dkeller',  email='dave.keller@example.com',      password_hash=pw)
    sarah   = User(username='smartin',  email='sarah.martin@example.com',     password_hash=pw)

    all_users = [admin, phil, john, mary, tom, kate, dave, sarah]
    db.session.add_all(all_users)
    db.session.commit()
    print(f"Created {len(all_users)} users")

    # ── Locations ────────────────────────────────────────────────────────────
    HUNTERWOODS  = 'Hunterwoods Shopping Center, 2324 Hunter Mill Rd, Reston, VA'
    ARTSPACE     = 'ArtSpace Parking Lot, 635 Herndon Pkwy, Herndon, VA'
    BIKE_LANE    = 'The Bike Lane, 11943 Lake Newport Rd, Reston, VA'
    LAKE_NEWPORT = 'Lake Newport Lake House, 1100 Lake Newport Rd, Reston, VA'
    RTC          = 'Reston Town Center Pavilion, 11900 Market St, Reston, VA'

    # ── RideWithGPS routes (real public RBC/NoVA routes — embeds will render) ──
    RWGPS_TUE_WORLDS   = 'https://ridewithgps.com/routes/35103917'  # Tour de Hunter Mill (long A)
    RWGPS_TUE_B        = 'https://ridewithgps.com/routes/35758396'  # RBC Fox Mill Group 2 extended (~27mi)
    RWGPS_WED_RAMBLE   = 'https://ridewithgps.com/routes/45147'     # RBC Tuesday Ride (~19mi, C-pace ramble)
    RWGPS_THU_B        = 'https://ridewithgps.com/routes/34495154'  # Leesburg area (~44mi B group)
    RWGPS_WOMENS_THU   = 'https://ridewithgps.com/routes/33309426'  # RBC Public Art Ride N+S Reston (~18mi)
    RWGPS_SAT_A_LEESB  = 'https://ridewithgps.com/routes/31848563'  # 55G Spokes+ Leesburg (~56mi A group)
    RWGPS_SAT_B_LEESB  = 'https://ridewithgps.com/routes/248407'    # Leesburg Loop (~23mi B/C)
    RWGPS_SAT_C        = 'https://ridewithgps.com/routes/32400962'  # Reston Mostly Bike Paths (C/easy)
    RWGPS_MIDDLEBURG   = 'https://ridewithgps.com/routes/39485933'  # Middleburg (~59mi +3584ft, A group)
    RWGPS_GOOSE_CREEK  = 'https://ridewithgps.com/routes/31799369'  # Middleburg Figure 8 (~57mi +4009ft)
    RWGPS_CENTURY_100  = 'https://ridewithgps.com/routes/16172906'  # RBC Century 2016 (~104mi)
    RWGPS_SUNDAY_EASY  = 'https://ridewithgps.com/routes/33309467'  # RBC Public Art Transit Area (~10mi easy)
    RWGPS_SPRING_KICK  = 'https://ridewithgps.com/routes/12422327'  # RBC March Century via Sycolin (group B/C start)

    # ── Rides ────────────────────────────────────────────────────────────────
    # Today: Monday Apr 20, 2026
    # Past:  Tue Apr 14, Thu Apr 16, Sat Apr 18
    # Week1: Tue Apr 21, Wed Apr 22, Thu Apr 23, Sat Apr 25, Sun Apr 26
    # Week2: Tue Apr 28, Wed Apr 29, Thu Apr 30, Sat May  2, Sun May  3
    # Week3: Tue May  5, Wed May  6, Thu May  7, Sat May  9
    # Week4: Tue May 12, Thu May 14, Sat May 16
    # Week5: Sat May 23
    # Special: Sat Aug 23 (Ken Thompson Century)

    rides = [

        # ── Past rides (give them signups so the history looks lived-in) ──────
        Ride(
            title='Tuesday Worlds — A Group',
            date=date(2026, 4, 14), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=2100, pace_category='A',
            ride_leader='Dave K.',
            route_url=RWGPS_TUE_WORLDS,
            description='Fast no-mercy Tuesday worlds. If you can hold the wheel, great. If not, see you Thursday.',
        ),
        Ride(
            title='Tuesday Evening Ride — B Group',
            date=date(2026, 4, 14), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=28, elevation_feet=1350, pace_category='B',
            ride_leader='Tom R.',
            route_url=RWGPS_TUE_B,
            description='Rolling route through Great Falls. Regroup at the top of difficult climbs.',
        ),
        Ride(
            title='Thursday Evening — B/C Group',
            date=date(2026, 4, 16), time=time(17, 0),
            meeting_location=ARTSPACE,
            distance_miles=30, elevation_feet=1500, pace_category='B',
            ride_leader='Sarah M.',
            route_url=RWGPS_THU_B,
        ),
        Ride(
            title='Saturday Club Ride — A Group',
            date=date(2026, 4, 18), time=time(8, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=58, elevation_feet=3400, pace_category='A',
            ride_leader='Dave K.',
            route_url=RWGPS_MIDDLEBURG,
            description='Middleburg loop. Long day in the saddle — bring two full bottles and a snack.',
        ),
        Ride(
            title='Saturday Club Ride — C Group',
            date=date(2026, 4, 18), time=time(8, 30),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=1900, pace_category='C',
            ride_leader='Linda H.',
            route_url=RWGPS_SAT_C,
        ),

        # ── Week 1: Apr 21–27 ────────────────────────────────────────────────
        Ride(
            title='Tuesday Worlds — A Group',
            date=date(2026, 4, 21), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=2100, pace_category='A',
            ride_leader='Dave K.',
            route_url=RWGPS_TUE_WORLDS,
        ),
        Ride(
            title='Tuesday Evening Ride — B Group',
            date=date(2026, 4, 21), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=28, elevation_feet=1350, pace_category='B',
            ride_leader='Tom R.',
            route_url=RWGPS_TUE_B,
            description='No-drop ride. We regroup at the top of hills and after traffic lights.',
        ),
        Ride(
            title='Wednesday Morning Ramble',
            date=date(2026, 4, 22), time=time(10, 0),
            meeting_location=BIKE_LANE,
            distance_miles=25, elevation_feet=900, pace_category='C',
            ride_leader='Linda H.',
            route_url=RWGPS_WED_RAMBLE,
            description='Mid-week social spin. Coffee stop at the turnaround is highly likely.',
        ),
        Ride(
            title='Thursday Evening — B Group',
            date=date(2026, 4, 23), time=time(17, 0),
            meeting_location=ARTSPACE,
            distance_miles=30, elevation_feet=1500, pace_category='B',
            ride_leader='Mark W.',
            route_url=RWGPS_THU_B,
        ),
        Ride(
            title="Women's Thursday Ride",
            date=date(2026, 4, 23), time=time(18, 0),
            meeting_location=LAKE_NEWPORT,
            distance_miles=18, elevation_feet=600, pace_category='D',
            ride_leader='Jennifer L.',
            route_url=RWGPS_WOMENS_THU,
            description='All-women, all-paces welcome. Supportive group, no one gets dropped.',
        ),
        Ride(
            title='Saturday A Ride to Leesburg & Back',
            date=date(2026, 4, 25), time=time(8, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=55, elevation_feet=3200, pace_category='A',
            ride_leader='Dave K.',
            route_url=RWGPS_SAT_A_LEESB,
            description='Double loop through Loudoun County back roads. Regroup at the base of Snickersville Turnpike.',
        ),
        Ride(
            title='Saturday B Ride to Leesburg & Back',
            date=date(2026, 4, 25), time=time(8, 30),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=1800, pace_category='B',
            ride_leader='Susan P.',
            route_url=RWGPS_SAT_B_LEESB,
        ),
        Ride(
            title='RBC Spring Kickoff Ride',
            date=date(2026, 4, 26), time=time(9, 0),
            meeting_location=BIKE_LANE,
            distance_miles=26, elevation_feet=750, pace_category='D',
            ride_leader='Bob N.',
            route_url=RWGPS_SPRING_KICK,
            description='Annual season opener. Recovery-pace loop, post-ride coffee, new members welcome.',
        ),

        # ── Week 2: Apr 28 – May 3 ───────────────────────────────────────────
        Ride(
            title='Tuesday Worlds — A Group',
            date=date(2026, 4, 28), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=2100, pace_category='A',
            ride_leader='Dave K.',
        ),
        Ride(
            title='Tuesday Evening Ride — B Group',
            date=date(2026, 4, 28), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=28, elevation_feet=1350, pace_category='B',
            ride_leader='Tom R.',
        ),
        Ride(
            title='Wednesday Morning Ramble',
            date=date(2026, 4, 29), time=time(10, 0),
            meeting_location=BIKE_LANE,
            distance_miles=22, elevation_feet=800, pace_category='C',
            ride_leader='Linda H.',
        ),
        Ride(
            title='Thursday Evening — B Group',
            date=date(2026, 4, 30), time=time(17, 0),
            meeting_location=ARTSPACE,
            distance_miles=32, elevation_feet=1600, pace_category='B',
            ride_leader='Mark W.',
        ),
        Ride(
            title="Women's Thursday Ride",
            date=date(2026, 4, 30), time=time(18, 0),
            meeting_location=LAKE_NEWPORT,
            distance_miles=18, elevation_feet=600, pace_category='D',
            ride_leader='Jennifer L.',
        ),
        Ride(
            title='Saturday Club Ride — A Group',
            date=date(2026, 5, 2), time=time(8, 0),
            meeting_location=RTC,
            distance_miles=62, elevation_feet=3800, pace_category='A',
            ride_leader='Chris T.',
            description='Goose Creek loop. 62 miles of Loudoun grind. Bring two bottles minimum.',
        ),
        Ride(
            title='Saturday Club Ride — C/D',
            date=date(2026, 5, 2), time=time(8, 30),
            meeting_location=RTC,
            distance_miles=30, elevation_feet=1100, pace_category='C',
            ride_leader='Susan P.',
        ),

        # ── Week 3: May 5–10 ─────────────────────────────────────────────────
        Ride(
            title='Tuesday Worlds — A Group',
            date=date(2026, 5, 5), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=40, elevation_feet=2200, pace_category='A',
            ride_leader='Dave K.',
        ),
        Ride(
            title='Tuesday Evening Ride — B Group',
            date=date(2026, 5, 5), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=28, elevation_feet=1350, pace_category='B',
            ride_leader='Tom R.',
        ),
        Ride(
            title='Wednesday Morning Ramble',
            date=date(2026, 5, 6), time=time(10, 0),
            meeting_location=BIKE_LANE,
            distance_miles=25, elevation_feet=900, pace_category='C',
            ride_leader='Linda H.',
        ),
        Ride(
            title='Thursday Evening — B Group',
            date=date(2026, 5, 7), time=time(17, 0),
            meeting_location=ARTSPACE,
            distance_miles=30, elevation_feet=1500, pace_category='B',
            ride_leader='Mark W.',
        ),
        Ride(
            title="Women's Thursday Ride",
            date=date(2026, 5, 7), time=time(18, 0),
            meeting_location=LAKE_NEWPORT,
            distance_miles=18, elevation_feet=600, pace_category='D',
            ride_leader='Jennifer L.',
        ),
        Ride(
            title='Saturday Club Ride — A/B',
            date=date(2026, 5, 9), time=time(8, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=50, elevation_feet=2900, pace_category='A',
            ride_leader='Dave K.',
            description='W&OD out and Loudoun back roads return. Fast and fun.',
        ),

        # ── Week 4: May 12–17 ────────────────────────────────────────────────
        Ride(
            title='Tuesday Worlds — A Group',
            date=date(2026, 5, 12), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=38, elevation_feet=2100, pace_category='A',
            ride_leader='Dave K.',
        ),
        Ride(
            title='Tuesday Evening Ride — B Group',
            date=date(2026, 5, 12), time=time(17, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=28, elevation_feet=1350, pace_category='B',
            ride_leader='Tom R.',
        ),
        Ride(
            title='Thursday Evening — B Group',
            date=date(2026, 5, 14), time=time(17, 0),
            meeting_location=ARTSPACE,
            distance_miles=30, elevation_feet=1500, pace_category='B',
            ride_leader='Mark W.',
        ),
        Ride(
            title="Women's Thursday Ride",
            date=date(2026, 5, 14), time=time(18, 0),
            meeting_location=LAKE_NEWPORT,
            distance_miles=20, elevation_feet=700, pace_category='D',
            ride_leader='Jennifer L.',
        ),
        Ride(
            title='Saturday Club Ride — A Group',
            date=date(2026, 5, 16), time=time(8, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=65, elevation_feet=4100, pace_category='A',
            ride_leader='Chris T.',
            description='Big day. Paris–Roubaix vibes in the Loudoun back roads. Not actually cobbles.',
        ),
        Ride(
            title='Saturday Club Ride — B Group',
            date=date(2026, 5, 16), time=time(8, 30),
            meeting_location=HUNTERWOODS,
            distance_miles=45, elevation_feet=2400, pace_category='B',
            ride_leader='Sarah M.',
        ),

        # ── Special event ─────────────────────────────────────────────────────
        Ride(
            title='43rd Ken Thompson Reston Century',
            date=date(2026, 8, 23), time=time(7, 0),
            meeting_location=HUNTERWOODS,
            distance_miles=100, elevation_feet=5800, pace_category='A',
            ride_leader='RBC Board',
            description=(
                'The flagship RBC event — 43 years running. '
                'Multiple route options: 25, 50, 75, and 100 miles. '
                'SAG support, rest stops, and post-ride celebration. '
                'Register in advance at restonbikeclub.org.'
            ),
        ),
    ]

    db.session.add_all(rides)
    db.session.commit()
    print(f"Created {len(rides)} rides")

    # ── Signups ──────────────────────────────────────────────────────────────
    def signup(ride, *users):
        for u in users:
            db.session.add(RideSignup(ride_id=ride.id, user_id=u.id))

    # Past rides — fully attended
    signup(rides[0], admin, phil, dave, sarah)          # Tue A Apr 14
    signup(rides[1], john, mary, tom, kate)             # Tue B Apr 14
    signup(rides[2], phil, john, tom, sarah)            # Thu B Apr 16
    signup(rides[3], admin, phil, dave, john)           # Sat A Apr 18
    signup(rides[4], mary, kate, tom, sarah)            # Sat C Apr 18

    # Upcoming — realistic pre-signups
    signup(rides[5],  admin, phil, dave)                # Tue A Apr 21
    signup(rides[6],  john, mary, tom, sarah)           # Tue B Apr 21
    signup(rides[7],  mary, kate, sarah)                # Wed Ramble
    signup(rides[8],  phil, john, tom)                  # Thu B Apr 23
    signup(rides[9],  mary, kate)                       # Women's Thu
    signup(rides[10], admin, phil, dave, john)          # Sat A/B Apr 25
    signup(rides[11], mary, tom, kate, sarah)           # Sat C Apr 25
    signup(rides[12], kate, sarah)                      # Sun Easy

    signup(rides[13], admin, dave)                      # Tue A Apr 28
    signup(rides[14], john, tom)                        # Tue B Apr 28
    signup(rides[16], phil, john)                       # Thu B Apr 30
    signup(rides[17], mary, kate)                       # Women's Thu Apr 30
    signup(rides[18], admin, phil, dave)                # Sat A May 2

    signup(rides[32], admin, phil, dave, john, sarah)   # Century Aug 23

    db.session.commit()
    print("Created signups")
    print("\nSeed complete!")
    print("\nLogin credentials (all use password: password123):")
    print("  admin@rbc.dev       — admin account")
    print("  phil@pcp.dev        — regular member")
    print("  john.smith@...      — regular member")
    print("  mary.baker@...      — regular member")
