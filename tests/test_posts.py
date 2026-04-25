"""Tests for club news/announcements (ClubPost CRUD)."""
import pytest
from app.models import ClubPost
from tests.conftest import login


def _login_admin(client, club_admin_user):
    login(client, email=club_admin_user.email)


class TestPostAdmin:
    def test_post_list_requires_admin(self, client, sample_club, regular_user):
        login(client, email=regular_user.email)
        r = client.get(f'/admin/clubs/{sample_club.slug}/posts', follow_redirects=True)
        assert r.status_code == 403

    def test_post_list_empty(self, client, sample_club, club_admin_user):
        _login_admin(client, club_admin_user)
        r = client.get(f'/admin/clubs/{sample_club.slug}/posts')
        assert r.status_code == 200
        assert b'No posts yet' in r.data

    def test_create_post(self, client, db, sample_club, club_admin_user):
        _login_admin(client, club_admin_user)
        r = client.post(f'/admin/clubs/{sample_club.slug}/posts/new', data={
            'title': 'Big Announcement',
            'body': 'We are doing a century next month!',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'Post published' in r.data
        post = ClubPost.query.filter_by(club_id=sample_club.id).first()
        assert post is not None
        assert post.title == 'Big Announcement'
        assert post.author_id == club_admin_user.id

    def test_edit_post(self, client, db, sample_club, club_admin_user):
        _login_admin(client, club_admin_user)
        post = ClubPost(club_id=sample_club.id, author_id=club_admin_user.id,
                        title='Old Title', body='Old body')
        db.session.add(post)
        db.session.commit()

        r = client.post(f'/admin/clubs/{sample_club.slug}/posts/{post.id}/edit', data={
            'title': 'New Title',
            'body': 'Updated body text',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'Post updated' in r.data
        db.session.refresh(post)
        assert post.title == 'New Title'

    def test_delete_post(self, client, db, sample_club, club_admin_user):
        _login_admin(client, club_admin_user)
        post = ClubPost(club_id=sample_club.id, author_id=club_admin_user.id,
                        title='Bye', body='Goodbye world')
        db.session.add(post)
        db.session.commit()
        post_id = post.id

        r = client.post(f'/admin/clubs/{sample_club.slug}/posts/{post_id}/delete',
                        follow_redirects=True)
        assert r.status_code == 200
        assert b'Post deleted' in r.data
        assert ClubPost.query.get(post_id) is None

    def test_post_wrong_club_404(self, client, db, sample_club, second_club, club_admin_user):
        """A post belonging to second_club cannot be accessed via sample_club's route."""
        _login_admin(client, club_admin_user)
        post = ClubPost(club_id=second_club.id, author_id=club_admin_user.id,
                        title='Other club post', body='...')
        db.session.add(post)
        db.session.commit()

        # Accessing via sample_club slug should 404 (post.club_id != sample_club.id)
        r = client.get(f'/admin/clubs/{sample_club.slug}/posts/{post.id}/edit')
        assert r.status_code == 404


class TestPostPublic:
    def test_posts_shown_on_club_home(self, client, db, sample_club, club_admin_user, mock_weather):
        post = ClubPost(club_id=sample_club.id, author_id=club_admin_user.id,
                        title='Upcoming Gran Fondo', body='Join us for the big ride.')
        db.session.add(post)
        db.session.commit()

        r = client.get(f'/clubs/{sample_club.slug}/')
        assert r.status_code == 200
        assert b'Upcoming Gran Fondo' in r.data
        assert b'Join us for the big ride.' in r.data

    def test_only_three_posts_shown(self, client, db, sample_club, club_admin_user, mock_weather):
        for i in range(5):
            db.session.add(ClubPost(club_id=sample_club.id, author_id=club_admin_user.id,
                                    title=f'Post {i}', body=f'Body {i}'))
        db.session.commit()

        r = client.get(f'/clubs/{sample_club.slug}/')
        assert r.status_code == 200
        # 3 shown, 2 not
        shown = sum(1 for i in range(5) if f'Post {i}'.encode() in r.data)
        assert shown == 3

    def test_no_news_section_when_no_posts(self, client, sample_club, mock_weather):
        r = client.get(f'/clubs/{sample_club.slug}/')
        assert r.status_code == 200
        assert b'Manage Posts' not in r.data
