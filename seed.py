"""
Cycling Clubs App — development seed data.
Run inside the container: python seed.py

Creates 3 clubs with realistic ride schedules, users, memberships, waivers, and signups.
"""
from datetime import date, time, datetime, timezone
from app import create_app
from app.extensions import db, bcrypt
from app.models import (User, Club, ClubMembership, ClubAdmin, ClubWaiver,
                         WaiverSignature, Ride, RideSignup)

app = create_app()

with app.app_context():
    # ── Wipe existing data (dev only) ─────────────────────────────────────────
    db.drop_all()
    db.create_all()
    print("Schema reset.")

    # ── Users ─────────────────────────────────────────────────────────────────
    pw = bcrypt.generate_password_hash('password123').decode()

    superadmin = User(username='superadmin', email='admin@cyclingclub.dev',      password_hash=pw, is_admin=True)
    phil       = User(username='phil',       email='phil@pcp.dev',               password_hash=pw, zip_code='20148', address='Ashburn, VA')
    jsmith     = User(username='jsmith',     email='john.smith@example.com',     password_hash=pw, zip_code='20191')
    mbaker     = User(username='mbaker',     email='mary.baker@example.com',     password_hash=pw, zip_code='20190')
    twheels    = User(username='twheels',    email='tom.wheels@example.com',     password_hash=pw, zip_code='20194')
    kroller    = User(username='kroller',    email='kate.roller@example.com',    password_hash=pw, zip_code='22030')
    dkeller    = User(username='dkeller',    email='dave.keller@example.com',    password_hash=pw, zip_code='20191')
    smartin    = User(username='smartin',    email='sarah.martin@example.com',   password_hash=pw, zip_code='20170')
    # NVCC users
    nvcc_admin = User(username='nvcc_admin', email='admin@nvcc.dev',             password_hash=pw)
    arider     = User(username='arider',     email='alex.rider@example.com',     password_hash=pw, zip_code='22101')
    bclimber   = User(username='bclimber',   email='beth.climber@example.com',   password_hash=pw, zip_code='22102')
    # Artemis users
    art_admin  = User(username='art_admin',  email='admin@artemis.dev',          password_hash=pw)
    cspinner   = User(username='cspinner',   email='claire.spin@example.com',    password_hash=pw, zip_code='22201')

    all_users = [superadmin, phil, jsmith, mbaker, twheels, kroller, dkeller, smartin,
                 nvcc_admin, arider, bclimber, art_admin, cspinner]
    db.session.add_all(all_users)
    db.session.commit()
    print(f"Created {len(all_users)} users")

    # ── Clubs ─────────────────────────────────────────────────────────────────
    rbc = Club(
        slug='rbc',
        name='Reston Bike Club',
        description=(
            'One of the largest cycling clubs in Northern Virginia. '
            'Weekly rides for all levels — Tuesday Worlds to leisurely Sunday spins. '
            'Home of the annual Ken Thompson Reston Century.'
        ),
        website='https://restonbikeclub.org',
        contact_email='info@restonbikeclub.org',
        address='Hunterwoods Shopping Center, 2324 Hunter Mill Rd',
        city='Reston', state='VA', zip_code='20191',
        lat=38.9376, lng=-77.3476,
    )
    nvcc = Club(
        slug='nvcc',
        name='Northern Virginia Cycling Club',
        description=(
            'Fast-paced road and gravel club based in McLean and the DC suburbs. '
            'Known for challenging Saturday hammerfests and weeknight criterium training.'
        ),
        website='https://example.com/nvcc',
        contact_email='info@nvcc.dev',
        address='McLean Community Center, 1234 Ingleside Ave',
        city='McLean', state='VA', zip_code='22101',
        lat=38.9339, lng=-77.1773,
        is_private=True,  # invite-only example
        theme_preset='ocean',
        theme_primary='#1a5276',
        theme_accent='#f39c12',
    )
    artemis = Club(
        slug='artemis',
        name='Artemis Cycling — Women\'s Club',
        description=(
            'Northern Virginia\'s premier women\'s cycling club. '
            'Supportive, no-drop rides for all fitness levels plus structured training for racers.'
        ),
        website='https://example.com/artemis',
        contact_email='info@artemis.dev',
        address='Ballston Common, 4238 Wilson Blvd',
        city='Arlington', state='VA', zip_code='22203',
        lat=38.8820, lng=-77.1128,
    )

    db.session.add_all([rbc, nvcc, artemis])
    db.session.commit()
    print("Created 3 clubs: rbc, nvcc, artemis")

    # ── Club admins ───────────────────────────────────────────────────────────
    db.session.add_all([
        ClubAdmin(user_id=dkeller.id,    club_id=rbc.id,     role='admin'),
        ClubAdmin(user_id=nvcc_admin.id, club_id=nvcc.id,    role='admin'),
        ClubAdmin(user_id=art_admin.id,  club_id=artemis.id, role='admin'),
        # Phil can manage rides at RBC but not settings
        ClubAdmin(user_id=phil.id,       club_id=rbc.id,     role='ride_manager'),
    ])
    db.session.commit()

    # ── Club memberships ──────────────────────────────────────────────────────
    def join(club, *users):
        for u in users:
            db.session.add(ClubMembership(user_id=u.id, club_id=club.id))

    join(rbc,     phil, jsmith, mbaker, twheels, kroller, dkeller, smartin)
    join(nvcc,    phil, arider, bclimber, dkeller)
    join(artemis, mbaker, kroller, smartin, cspinner, bclimber)
    db.session.commit()
    print("Created club memberships")

    # ── Club waivers ──────────────────────────────────────────────────────────
    yr = date.today().year

    rbc_waiver = ClubWaiver(
        club_id=rbc.id, year=yr,
        title=f'Reston Bike Club {yr} Liability Waiver & Rules',
        body=(
            'By signing this waiver I acknowledge that cycling involves risk of injury or death. '
            'I release the Reston Bike Club, its officers, and ride leaders from all liability. '
            'I agree to wear a helmet on all club rides, obey all traffic laws, '
            'and follow the ride leader\'s instructions. '
            'I confirm that my bicycle is in safe, road-worthy condition.'
        ),
    )
    nvcc_waiver = ClubWaiver(
        club_id=nvcc.id, year=yr,
        title=f'NVCC {yr} Participation Agreement',
        body=(
            'Participation in NVCC rides is at my own risk. '
            'I release NVCC from liability for any injury, loss, or damage sustained during club activities. '
            'I agree to ride predictably, call out hazards, and never overlap wheels on group rides. '
            'Helmets are mandatory. No earbuds in both ears.'
        ),
    )
    artemis_waiver = ClubWaiver(
        club_id=artemis.id, year=yr,
        title=f'Artemis Cycling {yr} Rider Agreement',
        body=(
            'I understand that cycling carries inherent risks. '
            'I release Artemis Cycling from all liability related to club rides and events. '
            'I agree to uphold the club\'s code of conduct: be supportive, no one gets dropped intentionally, '
            'helmets required, and always ride with a buddy on solo training rides.'
        ),
    )
    db.session.add_all([rbc_waiver, nvcc_waiver, artemis_waiver])
    db.session.commit()
    print("Created club waivers")

    # Phil has signed RBC waiver; most others haven't (to test the gate)
    db.session.add(WaiverSignature(user_id=phil.id, club_id=rbc.id,
                                   waiver_id=rbc_waiver.id, year=yr))
    db.session.add(WaiverSignature(user_id=dkeller.id, club_id=rbc.id,
                                   waiver_id=rbc_waiver.id, year=yr))
    db.session.add(WaiverSignature(user_id=arider.id, club_id=nvcc.id,
                                   waiver_id=nvcc_waiver.id, year=yr))
    db.session.commit()
    print("Created waiver signatures")

    # ── RBC Rides ─────────────────────────────────────────────────────────────
    HUNTERWOODS  = 'Hunterwoods Shopping Center, 2324 Hunter Mill Rd, Reston, VA'
    ARTSPACE     = 'ArtSpace Parking Lot, 635 Herndon Pkwy, Herndon, VA'
    BIKE_LANE    = 'The Bike Lane, 11943 Lake Newport Rd, Reston, VA'
    LAKE_NEWPORT = 'Lake Newport Lake House, 1100 Lake Newport Rd, Reston, VA'

    # Real public RBC/NoVA RideWithGPS routes
    RWGPS_TUE_WORLDS  = 'https://ridewithgps.com/routes/35103917'
    RWGPS_TUE_B       = 'https://ridewithgps.com/routes/35758396'
    RWGPS_WED_RAMBLE  = 'https://ridewithgps.com/routes/45147'
    RWGPS_THU_B       = 'https://ridewithgps.com/routes/34495154'
    RWGPS_WOMENS_THU  = 'https://ridewithgps.com/routes/33309426'
    RWGPS_SAT_A_LEESB = 'https://ridewithgps.com/routes/31848563'
    RWGPS_SAT_B_LEESB = 'https://ridewithgps.com/routes/248407'
    RWGPS_SAT_C       = 'https://ridewithgps.com/routes/32400962'
    RWGPS_MIDDLEBURG  = 'https://ridewithgps.com/routes/39485933'
    RWGPS_GOOSE_CREEK = 'https://ridewithgps.com/routes/31799369'
    RWGPS_CENTURY_100 = 'https://ridewithgps.com/routes/16172906'
    RWGPS_SUNDAY_EASY = 'https://ridewithgps.com/routes/33309467'
    RWGPS_SPRING_KICK = 'https://ridewithgps.com/routes/12422327'

    rbc_rides = [
        # Past rides
        Ride(club_id=rbc.id, title='Tuesday Worlds — A Group',
             date=date(2026, 4, 14), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=38, elevation_feet=2100, pace_category='A',
             ride_leader='Dave K.', route_url=RWGPS_TUE_WORLDS,
             description='Fast no-mercy Tuesday worlds.'),
        Ride(club_id=rbc.id, title='Tuesday Evening — B Group',
             date=date(2026, 4, 14), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=28, elevation_feet=1350, pace_category='B',
             ride_leader='Tom R.', route_url=RWGPS_TUE_B,
             description='Rolling route through Great Falls. Regroup at the top of difficult climbs.'),
        Ride(club_id=rbc.id, title='Thursday Evening — B/C Group',
             date=date(2026, 4, 16), time=time(17, 0), meeting_location=ARTSPACE,
             distance_miles=30, elevation_feet=1500, pace_category='B',
             ride_leader='Sarah M.', route_url=RWGPS_THU_B),
        Ride(club_id=rbc.id, title='Saturday Club Ride — A Group',
             date=date(2026, 4, 18), time=time(8, 0), meeting_location=HUNTERWOODS,
             distance_miles=58, elevation_feet=3400, pace_category='A',
             ride_leader='Dave K.', route_url=RWGPS_MIDDLEBURG,
             description='Middleburg loop. Long day in the saddle — bring two full bottles and a snack.'),
        Ride(club_id=rbc.id, title='Saturday Club Ride — C Group',
             date=date(2026, 4, 18), time=time(8, 30), meeting_location=HUNTERWOODS,
             distance_miles=38, elevation_feet=1900, pace_category='C',
             ride_leader='Linda H.', route_url=RWGPS_SAT_C),
        # Week 1: Apr 21–27
        Ride(club_id=rbc.id, title='Tuesday Worlds — A Group',
             date=date(2026, 4, 21), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=38, elevation_feet=2100, pace_category='A',
             ride_leader='Dave K.', route_url=RWGPS_TUE_WORLDS),
        Ride(club_id=rbc.id, title='Tuesday Evening — B Group',
             date=date(2026, 4, 21), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=28, elevation_feet=1350, pace_category='B',
             ride_leader='Tom R.', route_url=RWGPS_TUE_B,
             description='No-drop ride. Regroup at the top of hills.'),
        Ride(club_id=rbc.id, title='Wednesday Morning Ramble',
             date=date(2026, 4, 22), time=time(10, 0), meeting_location=BIKE_LANE,
             distance_miles=25, elevation_feet=900, pace_category='C',
             ride_leader='Linda H.', route_url=RWGPS_WED_RAMBLE,
             description='Mid-week social spin. Coffee stop at the turnaround is highly likely.'),
        Ride(club_id=rbc.id, title='Thursday Evening — B Group',
             date=date(2026, 4, 23), time=time(17, 0), meeting_location=ARTSPACE,
             distance_miles=30, elevation_feet=1500, pace_category='B',
             ride_leader='Mark W.', route_url=RWGPS_THU_B),
        Ride(club_id=rbc.id, title="Women's Thursday Ride",
             date=date(2026, 4, 23), time=time(18, 0), meeting_location=LAKE_NEWPORT,
             distance_miles=18, elevation_feet=600, pace_category='D',
             ride_leader='Jennifer L.', route_url=RWGPS_WOMENS_THU,
             description='All-women, all-paces welcome. No one gets dropped.'),
        Ride(club_id=rbc.id, title='Saturday A Ride to Leesburg & Back',
             date=date(2026, 4, 25), time=time(8, 0), meeting_location=HUNTERWOODS,
             distance_miles=55, elevation_feet=3200, pace_category='A',
             ride_leader='Dave K.', route_url=RWGPS_SAT_A_LEESB,
             description='Double loop through Loudoun County back roads.'),
        Ride(club_id=rbc.id, title='Saturday B Ride to Leesburg & Back',
             date=date(2026, 4, 25), time=time(8, 30), meeting_location=HUNTERWOODS,
             distance_miles=38, elevation_feet=1800, pace_category='B',
             ride_leader='Susan P.', route_url=RWGPS_SAT_B_LEESB),
        Ride(club_id=rbc.id, title='RBC Spring Kickoff Ride',
             date=date(2026, 4, 26), time=time(9, 0), meeting_location=BIKE_LANE,
             distance_miles=26, elevation_feet=750, pace_category='D',
             ride_leader='Bob N.', route_url=RWGPS_SPRING_KICK,
             description='Annual season opener. Recovery-pace loop, post-ride coffee, new members welcome.'),
        # Week 2
        Ride(club_id=rbc.id, title='Tuesday Worlds — A Group',
             date=date(2026, 4, 28), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=38, elevation_feet=2100, pace_category='A', ride_leader='Dave K.'),
        Ride(club_id=rbc.id, title='Tuesday Evening — B Group',
             date=date(2026, 4, 28), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=28, elevation_feet=1350, pace_category='B', ride_leader='Tom R.'),
        Ride(club_id=rbc.id, title='Wednesday Morning Ramble',
             date=date(2026, 4, 29), time=time(10, 0), meeting_location=BIKE_LANE,
             distance_miles=22, elevation_feet=800, pace_category='C', ride_leader='Linda H.'),
        Ride(club_id=rbc.id, title='Thursday Evening — B Group',
             date=date(2026, 4, 30), time=time(17, 0), meeting_location=ARTSPACE,
             distance_miles=32, elevation_feet=1600, pace_category='B', ride_leader='Mark W.'),
        Ride(club_id=rbc.id, title="Women's Thursday Ride",
             date=date(2026, 4, 30), time=time(18, 0), meeting_location=LAKE_NEWPORT,
             distance_miles=18, elevation_feet=600, pace_category='D', ride_leader='Jennifer L.'),
        Ride(club_id=rbc.id, title='Saturday Club Ride — A Group',
             date=date(2026, 5, 2), time=time(8, 0), meeting_location=HUNTERWOODS,
             distance_miles=62, elevation_feet=3800, pace_category='A', ride_leader='Chris T.',
             route_url=RWGPS_GOOSE_CREEK,
             description='Goose Creek loop. 62 miles of Loudoun grind.'),
        Ride(club_id=rbc.id, title='Saturday Club Ride — C/D',
             date=date(2026, 5, 2), time=time(8, 30), meeting_location=HUNTERWOODS,
             distance_miles=30, elevation_feet=1100, pace_category='C', ride_leader='Susan P.',
             route_url=RWGPS_SAT_C),
        # Week 3
        Ride(club_id=rbc.id, title='Tuesday Worlds — A Group',
             date=date(2026, 5, 5), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=40, elevation_feet=2200, pace_category='A', ride_leader='Dave K.',
             route_url=RWGPS_TUE_WORLDS),
        Ride(club_id=rbc.id, title='Tuesday Evening — B Group',
             date=date(2026, 5, 5), time=time(17, 0), meeting_location=HUNTERWOODS,
             distance_miles=28, elevation_feet=1350, pace_category='B', ride_leader='Tom R.',
             route_url=RWGPS_TUE_B),
        Ride(club_id=rbc.id, title='Wednesday Morning Ramble',
             date=date(2026, 5, 6), time=time(10, 0), meeting_location=BIKE_LANE,
             distance_miles=25, elevation_feet=900, pace_category='C', ride_leader='Linda H.',
             route_url=RWGPS_WED_RAMBLE),
        Ride(club_id=rbc.id, title='Thursday Evening — B Group',
             date=date(2026, 5, 7), time=time(17, 0), meeting_location=ARTSPACE,
             distance_miles=30, elevation_feet=1500, pace_category='B', ride_leader='Mark W.',
             route_url=RWGPS_THU_B),
        Ride(club_id=rbc.id, title="Women's Thursday Ride",
             date=date(2026, 5, 7), time=time(18, 0), meeting_location=LAKE_NEWPORT,
             distance_miles=18, elevation_feet=600, pace_category='D', ride_leader='Jennifer L.',
             route_url=RWGPS_WOMENS_THU),
        Ride(club_id=rbc.id, title='Saturday Club Ride — A/B',
             date=date(2026, 5, 9), time=time(8, 0), meeting_location=HUNTERWOODS,
             distance_miles=50, elevation_feet=2900, pace_category='A', ride_leader='Dave K.',
             description='W&OD out and Loudoun back roads return.'),
        # Special event
        Ride(club_id=rbc.id, title='43rd Ken Thompson Reston Century',
             date=date(2026, 8, 23), time=time(7, 0), meeting_location=HUNTERWOODS,
             distance_miles=100, elevation_feet=5800, pace_category='A',
             ride_leader='RBC Board', route_url=RWGPS_CENTURY_100,
             description=(
                 'The flagship RBC event — 43 years running. '
                 'Multiple route options: 25, 50, 75, and 100 miles. '
                 'SAG support, rest stops, and post-ride celebration.'
             )),
    ]

    # ── NVCC Rides ────────────────────────────────────────────────────────────
    MCLEAN_CC    = 'McLean Community Center, 1234 Ingleside Ave, McLean, VA'
    GREAT_FALLS  = 'Great Falls Park Entrance, Georgetown Pike, Great Falls, VA'

    nvcc_rides = [
        Ride(club_id=nvcc.id, title='Thursday Night Worlds',
             date=date(2026, 4, 23), time=time(18, 0), meeting_location=MCLEAN_CC,
             distance_miles=32, elevation_feet=1800, pace_category='A',
             ride_leader='Alex R.',
             description='Fast hammerfest on the Chain Bridge loop. No drop — just no mercy.'),
        Ride(club_id=nvcc.id, title='Saturday Great Falls Hammerfest',
             date=date(2026, 4, 25), time=time(7, 30), meeting_location=MCLEAN_CC,
             distance_miles=60, elevation_feet=4200, pace_category='A',
             ride_leader='Beth C.',
             description='The signature NVCC ride. Plan for 3+ hours.'),
        Ride(club_id=nvcc.id, title='Sunday Recovery Spin',
             date=date(2026, 4, 26), time=time(9, 0), meeting_location=GREAT_FALLS,
             distance_miles=28, elevation_feet=900, pace_category='C',
             ride_leader='Alex R.',
             description='Easy legs after Saturday. Coffee stop guaranteed.'),
        Ride(club_id=nvcc.id, title='Thursday Night Worlds',
             date=date(2026, 4, 30), time=time(18, 0), meeting_location=MCLEAN_CC,
             distance_miles=32, elevation_feet=1800, pace_category='A', ride_leader='Alex R.'),
        Ride(club_id=nvcc.id, title='Saturday Great Falls Hammerfest',
             date=date(2026, 5, 2), time=time(7, 30), meeting_location=MCLEAN_CC,
             distance_miles=65, elevation_feet=4500, pace_category='A', ride_leader='Beth C.',
             description='Extended loop this week — Potomac Heritage Trail connection.'),
        Ride(club_id=nvcc.id, title='Thursday Night Worlds',
             date=date(2026, 5, 7), time=time(18, 0), meeting_location=MCLEAN_CC,
             distance_miles=32, elevation_feet=1800, pace_category='A', ride_leader='Alex R.'),
    ]

    # ── Artemis Rides ─────────────────────────────────────────────────────────
    BALLSTON     = 'Ballston Common, 4238 Wilson Blvd, Arlington, VA'
    ROSSLYN      = 'Rosslyn Metro, 1700 N Moore St, Arlington, VA'

    artemis_rides = [
        Ride(club_id=artemis.id, title='Tuesday Empowerment Ride',
             date=date(2026, 4, 22), time=time(18, 30), meeting_location=BALLSTON,
             distance_miles=20, elevation_feet=700, pace_category='C',
             ride_leader='Claire S.',
             description='All paces welcome. Supportive group, we regroup at every light.'),
        Ride(club_id=artemis.id, title='Saturday Training Ride — Intermediate',
             date=date(2026, 4, 25), time=time(8, 0), meeting_location=ROSSLYN,
             distance_miles=42, elevation_feet=2100, pace_category='B',
             ride_leader='Beth C.',
             description='Mount Vernon trail out, back roads return. Skills focus: paceline.'),
        Ride(club_id=artemis.id, title='Saturday Training Ride — Advanced',
             date=date(2026, 4, 25), time=time(8, 0), meeting_location=ROSSLYN,
             distance_miles=55, elevation_feet=3100, pace_category='A',
             ride_leader='Claire S.',
             description='Race prep ride. Bring race legs.'),
        Ride(club_id=artemis.id, title='Tuesday Empowerment Ride',
             date=date(2026, 4, 29), time=time(18, 30), meeting_location=BALLSTON,
             distance_miles=20, elevation_feet=700, pace_category='C', ride_leader='Claire S.'),
        Ride(club_id=artemis.id, title='Saturday Training Ride — Intermediate',
             date=date(2026, 5, 2), time=time(8, 0), meeting_location=ROSSLYN,
             distance_miles=40, elevation_feet=2000, pace_category='B', ride_leader='Beth C.'),
        Ride(club_id=artemis.id, title='New Rider Orientation Ride',
             date=date(2026, 5, 3), time=time(10, 0), meeting_location=BALLSTON,
             distance_miles=12, elevation_feet=300, pace_category='D',
             ride_leader='Claire S.',
             description='Never ridden in a group before? This is for you. Max 12mph, fully no-drop.'),
    ]

    all_rides = rbc_rides + nvcc_rides + artemis_rides
    db.session.add_all(all_rides)
    db.session.commit()
    print(f"Created {len(all_rides)} rides ({len(rbc_rides)} RBC, {len(nvcc_rides)} NVCC, {len(artemis_rides)} Artemis)")

    # ── Signups ───────────────────────────────────────────────────────────────
    def signup(ride, *users):
        for u in users:
            db.session.add(RideSignup(ride_id=ride.id, user_id=u.id))

    # RBC past rides
    signup(rbc_rides[0],  dkeller, phil, smartin)
    signup(rbc_rides[1],  jsmith, mbaker, twheels)
    signup(rbc_rides[2],  phil, jsmith, twheels)
    signup(rbc_rides[3],  dkeller, phil, jsmith)
    signup(rbc_rides[4],  mbaker, kroller, twheels)

    # RBC upcoming
    signup(rbc_rides[5],  dkeller, phil)
    signup(rbc_rides[6],  jsmith, mbaker, twheels, smartin)
    signup(rbc_rides[7],  mbaker, kroller, smartin)
    signup(rbc_rides[8],  phil, jsmith, twheels)
    signup(rbc_rides[9],  mbaker, kroller)
    signup(rbc_rides[10], dkeller, phil, jsmith)
    signup(rbc_rides[11], mbaker, twheels, kroller)
    signup(rbc_rides[25], dkeller, phil, jsmith, smartin)  # Century

    # NVCC
    signup(nvcc_rides[0], arider, bclimber, phil)
    signup(nvcc_rides[1], arider, bclimber)
    signup(nvcc_rides[2], arider, phil)

    # Artemis
    signup(artemis_rides[0], mbaker, kroller, cspinner, bclimber)
    signup(artemis_rides[1], kroller, bclimber)
    signup(artemis_rides[2], cspinner)

    db.session.commit()
    print("Created signups")

    print("\nSeed complete!")
    print("\nLogin credentials (all use password: password123):")
    print("  superadmin@cyclingclub.dev  — global superadmin")
    print("  phil@pcp.dev                — member of RBC + NVCC")
    print("  dave.keller@...             — RBC club admin")
    print("  admin@nvcc.dev              — NVCC club admin")
    print("  admin@artemis.dev           — Artemis club admin")
    print("  john.smith@...              — RBC member")
    print("  mary.baker@...              — RBC + Artemis member")
