import pytest
from rest_framework.test import APIClient

from src.authentication.models import User


@pytest.mark.django_db
def test_public_registration_supports_tourists_but_never_admins():
    client = APIClient()
    tourist = client.post('/api/v1/auth/register/', {
        'username': 'safe-tourist', 'email': 'tourist@example.com',
        'password': 'SafeTourist123!', 'first_name': 'Safe',
    })
    assert tourist.status_code == 201
    assert tourist.data['role'] == User.Roles.TOURIST

    admin = client.post('/api/v1/auth/register/', {
        'username': 'fake-admin', 'email': 'admin@example.com',
        'password': 'FakeAdmin123!', 'role': User.Roles.ADMIN,
    })
    assert admin.status_code == 400
    assert not User.objects.filter(email='admin@example.com').exists()


@pytest.mark.django_db
def test_guide_registration_requires_licence_and_creates_profile():
    client = APIClient()
    missing = client.post('/api/v1/auth/register/', {
        'username': 'guide-one', 'email': 'guide@example.com',
        'password': 'GuidePassword123!', 'role': User.Roles.GUIDE,
    })
    assert missing.status_code == 400

    created = client.post('/api/v1/auth/register/', {
        'username': 'guide-one', 'email': 'guide@example.com',
        'password': 'GuidePassword123!', 'role': User.Roles.GUIDE,
        'license_number': 'NTB-1234', 'bio': 'Kathmandu cultural guide.',
        'service_areas': ['Kathmandu Valley'],
    })
    assert created.status_code == 201
    user = User.objects.get(email='guide@example.com')
    assert user.guide_profile.license_number == 'NTB-1234'
    assert user.is_guide_verified is False


@pytest.mark.django_db
def test_user_cannot_read_or_update_another_profile():
    owner = User.objects.create_user(username='owner', email='owner@example.com', password='Password123!')
    stranger = User.objects.create_user(username='stranger', email='stranger@example.com', password='Password123!')
    client = APIClient()
    client.force_authenticate(owner)
    assert client.get(f'/api/v1/auth/users/{stranger.pk}/').status_code in (403, 404)
    assert client.patch(f'/api/v1/auth/users/{stranger.pk}/', {'first_name': 'Changed'}).status_code in (403, 404)
    stranger.refresh_from_db()
    assert stranger.first_name == ''


@pytest.mark.django_db
def test_preferences_and_password_change_are_owned_by_current_user():
    user = User.objects.create_user(username='settings', email='settings@example.com', password='OldPassword123!')
    client = APIClient()
    client.force_authenticate(user)
    initial = client.get('/api/v1/auth/users/preferences/')
    assert initial.status_code == 200
    assert initial.data['currency'] == 'NPR'
    response = client.patch('/api/v1/auth/users/preferences/', {'currency': 'USD', 'push_notifications': False})
    assert response.status_code == 200
    assert response.data['currency'] == 'USD'
    changed = client.post('/api/v1/auth/users/change-password/', {
        'current_password': 'OldPassword123!', 'new_password': 'NewPassword456!'
    })
    assert changed.status_code == 200
    user.refresh_from_db()
    assert user.check_password('NewPassword456!')


@pytest.mark.django_db
def test_guide_can_read_profile_without_entering_edit_mode():
    guide = User.objects.create_user(
        username='profile-guide', email='profile-guide@example.com',
        password='GuidePassword123!', role=User.Roles.GUIDE,
    )
    guide.guide_profile.license_number = 'NTB-READ-ONE'
    guide.guide_profile.save()
    client = APIClient()
    client.force_authenticate(guide)

    response = client.get('/api/v1/auth/users/guide-profile/')

    assert response.status_code == 200
    assert response.data['license_number'] == 'NTB-READ-ONE'
