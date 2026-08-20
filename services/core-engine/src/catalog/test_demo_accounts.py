"""The seeded demo accounts must actually be able to log in.

`get_or_create` does not hash a password, so demo users used to be created with
an EMPTY password hash. They existed, they owned bookings, they showed up in the
admin — and no one could ever sign in as them, which is only discoverable by
trying. The whole point of these accounts is the demonstration login, so the
invariant is worth a test rather than a docstring.
"""
from __future__ import annotations

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management.color import no_style
from django.core.management.base import OutputWrapper
from rest_framework.test import APIClient

from src.catalog.management.commands.seed_from_dataset import (
    DEMO_PASSWORDS,
    Command,
)

User = get_user_model()


def _seed_accounts() -> None:
    """Run just the account step — it needs no dataset files."""
    command = Command()
    command.stdout = OutputWrapper(io.StringIO())
    command.style = no_style()
    command._seed_demo_accounts()


@pytest.mark.django_db
@pytest.mark.parametrize("email", sorted(DEMO_PASSWORDS))
def test_every_demo_account_can_obtain_a_token(email):
    _seed_accounts()

    resp = APIClient().post(
        "/api/v1/auth/token/",
        {"email": email, "password": DEMO_PASSWORDS[email]},
        format="json",
    )
    assert resp.status_code == 200, f"{email} could not log in: {resp.content!r}"
    assert resp.json()["access"]


@pytest.mark.django_db
def test_demo_accounts_have_the_roles_their_features_require():
    _seed_accounts()

    # role=GUIDE is not cosmetic: BookingSession.clean() rejects an assigned
    # guide without it, and IsVerifiedGuide checks both role and verification.
    guide = User.objects.get(email="guide@guideu.local")
    assert guide.role == User.Roles.GUIDE
    assert guide.is_guide_verified
    assert hasattr(guide, "guide_profile")

    admin = User.objects.get(email="admin@guideu.local")
    assert admin.is_staff and admin.is_superuser
    assert admin.role == User.Roles.ADMIN

    assert User.objects.get(email="tourist@guideu.local").role == User.Roles.TOURIST


@pytest.mark.django_db
def test_reseeding_repairs_an_account_rather_than_skipping_it():
    """A re-run before a demo must restore known credentials, not preserve drift."""
    _seed_accounts()
    user = User.objects.get(email="tourist@guideu.local")
    user.set_password("something-else")
    user.role = User.Roles.ADMIN
    user.save()

    _seed_accounts()

    user.refresh_from_db()
    assert user.check_password(DEMO_PASSWORDS["tourist@guideu.local"])
    assert user.role == User.Roles.TOURIST
