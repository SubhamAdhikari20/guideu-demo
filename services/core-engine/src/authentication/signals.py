from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from src.common.events import Channels, publish_event
from .models import GuideProfile, TouristProfile, User, UserPreferences


@receiver(post_save, sender=User)
def create_profiles_for_user(sender: type[User], instance: User, created: bool, **kwargs: Any) -> None:
    if created:
        if instance.role == User.Roles.GUIDE:
            GuideProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Roles.TOURIST:
            TouristProfile.objects.get_or_create(user=instance)
        UserPreferences.objects.get_or_create(user=instance)
        publish_event(Channels.USER, {'event': 'user.created', 'user_id': instance.pk, 'role': instance.role})
