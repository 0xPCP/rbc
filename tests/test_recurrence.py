"""
Tests for recurring ride instance generation.
"""
import pytest
from datetime import date, time, timedelta
from app.models import Ride
from app.recurrence import generate_instances, delete_future_instances, WEEKS_AHEAD


@pytest.fixture
def recurring_ride(db, sample_club):
    """A recurring ride template on next Tuesday."""
    today = date.today()
    next_monday = today + timedelta(days=7 - today.weekday())
    next_tuesday = next_monday + timedelta(days=1)
    ride = Ride(
        club_id=sample_club.id,
        title='Weekly Tuesday Ride',
        date=next_tuesday,
        time=time(17, 0),
        meeting_location='Hunterwoods',
        distance_miles=38.0,
        pace_category='A',
        is_recurring=True,
    )
    db.session.add(ride)
    db.session.commit()
    return ride


@pytest.fixture
def one_shot_ride(db, sample_club):
    """A non-recurring ride."""
    ride = Ride(
        club_id=sample_club.id,
        title='One-Off Ride',
        date=date.today() + timedelta(days=5),
        time=time(8, 0),
        meeting_location='Somewhere',
        distance_miles=20.0,
        pace_category='B',
        is_recurring=False,
    )
    db.session.add(ride)
    db.session.commit()
    return ride


class TestGenerateInstances:
    def test_generates_correct_count(self, app, db, recurring_ride):
        created = generate_instances(recurring_ride, weeks=4)
        assert len(created) == 4

    def test_instances_are_weekly(self, app, db, recurring_ride):
        created = generate_instances(recurring_ride, weeks=4)
        dates = sorted(r.date for r in created)
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 7

    def test_instances_same_weekday_as_template(self, app, db, recurring_ride):
        created = generate_instances(recurring_ride, weeks=4)
        for instance in created:
            assert instance.date.weekday() == recurring_ride.date.weekday()

    def test_instances_linked_to_template(self, app, db, recurring_ride):
        created = generate_instances(recurring_ride, weeks=4)
        for instance in created:
            assert instance.recurrence_parent_id == recurring_ride.id
            assert instance.is_recurring is False

    def test_instances_inherit_ride_fields(self, app, db, recurring_ride):
        created = generate_instances(recurring_ride, weeks=2)
        for instance in created:
            assert instance.title == recurring_ride.title
            assert instance.pace_category == recurring_ride.pace_category
            assert instance.meeting_location == recurring_ride.meeting_location

    def test_idempotent_no_duplicates(self, app, db, recurring_ride):
        generate_instances(recurring_ride, weeks=4)
        generate_instances(recurring_ride, weeks=4)
        count = Ride.query.filter_by(recurrence_parent_id=recurring_ride.id).count()
        assert count == 4

    def test_non_recurring_ride_generates_nothing(self, app, db, one_shot_ride):
        created = generate_instances(one_shot_ride)
        assert created == []

    def test_instance_cannot_generate_sub_instances(self, app, db, recurring_ride):
        instances = generate_instances(recurring_ride, weeks=1)
        sub = generate_instances(instances[0])
        assert sub == []


class TestDeleteFutureInstances:
    def test_deletes_future_instances(self, app, db, recurring_ride):
        generate_instances(recurring_ride, weeks=4)
        deleted = delete_future_instances(recurring_ride)
        assert deleted == 4
        assert Ride.query.filter_by(recurrence_parent_id=recurring_ride.id).count() == 0

    def test_does_not_delete_past_instances(self, app, db, sample_club, recurring_ride):
        # Manually create a past instance
        past = Ride(
            club_id=sample_club.id,
            title='Weekly Tuesday Ride',
            date=date.today() - timedelta(days=7),
            time=time(17, 0),
            meeting_location='Hunterwoods',
            distance_miles=38.0,
            pace_category='A',
            is_recurring=False,
            recurrence_parent_id=recurring_ride.id,
        )
        db.session.add(past)
        db.session.commit()
        delete_future_instances(recurring_ride)
        assert Ride.query.filter_by(recurrence_parent_id=recurring_ride.id).count() == 1
