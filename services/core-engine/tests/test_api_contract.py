"""Contract tests that catch whole classes of routing bug at once.

These exist because of a real defect: the API is mounted under
``api/<version>/``, so Django passes ``version="v1"`` into every view handler.
Any handler declared as ``def handler(self, request)`` — without ``**kwargs`` —
raises ``TypeError`` on *every* request. Fourteen custom ``@action`` routes were
broken this way, including ``/auth/users/me/``, ``/payments/{id}/confirm/`` and
the scam-report moderation actions, and nothing caught it because each
individual endpoint lacked a test.

Rather than add fourteen near-identical tests, these walk the URL conf itself,
so a handler added later with the wrong signature fails here immediately.
"""
from __future__ import annotations

import inspect

import pytest
from django.urls import get_resolver
from rest_framework.test import APIClient

from src.authentication.models import User


def _api_view_handlers() -> dict[type, set[str]]:
    """Map each mounted DRF view class to every handler name routed to it.

    A viewset appears under several URL patterns — list, detail, and one per
    ``@action`` — and each carries its own ``actions`` map. The handler names
    must be unioned across all of them, or the extra actions (exactly the ones
    that were broken) are never inspected.
    """
    handlers: dict[type, set[str]] = {}
    for entry in get_resolver().url_patterns:
        _collect(entry, handlers)
    return handlers


def _collect(entry, handlers: dict[type, set[str]], depth: int = 0) -> None:
    if depth > 5:
        return
    nested = getattr(entry, "url_patterns", None)
    if nested is not None:
        for child in nested:
            _collect(child, handlers, depth + 1)
        return

    callback = getattr(entry, "callback", None)
    cls = getattr(callback, "cls", None)
    if cls is None:
        return
    # Viewset routes name their handlers; plain APIViews use the HTTP verb.
    names = set(getattr(callback, "actions", {}).values()) or {
        verb for verb in ("get", "post", "put", "patch", "delete") if hasattr(cls, verb)
    }
    handlers.setdefault(cls, set()).update(names)


def test_every_api_handler_accepts_url_kwargs():
    """No view handler may reject the ``version`` kwarg the URL conf supplies."""
    offenders = []
    for cls, handler_names in _api_view_handlers().items():
        for handler_name in handler_names:
            handler = getattr(cls, handler_name, None)
            if handler is None or not callable(handler):
                continue
            params = inspect.signature(handler).parameters
            takes_var_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
            if not takes_var_kw:
                offenders.append(
                    f"{cls.__module__}.{cls.__name__}.{handler_name}{inspect.signature(handler)}"
                )

    assert not offenders, (
        "These handlers will raise TypeError because the API is mounted under "
        "api/<version>/ and Django passes version= to every handler. Add "
        "*args, **kwargs:\n  " + "\n  ".join(sorted(offenders))
    )


@pytest.fixture
def auth_client(db):
    user = User.objects.create_user(email="contract@test.com", username="contract", password="ContractTest1!")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/users/me/",
        "/api/v1/gamification/awards/me/",
        "/api/v1/gamification/awards/leaderboard/",
        "/api/v1/notifications/notifications/unread_count/",
        "/api/v1/reviews/reviews/summary/",
    ],
)
def test_custom_actions_respond(auth_client, path):
    """The signed-in user's own routes must answer, not 403 or 500.

    ``/auth/users/me/`` regressed to 403 once because the viewset's
    ``get_permissions`` overrode the ``@action`` decorator's own
    ``permission_classes`` and fell through to an admin-only default.
    """
    response = auth_client.get(path)
    assert response.status_code == 200, f"{path} returned {response.status_code}: {response.content[:200]}"
