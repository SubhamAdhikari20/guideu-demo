from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import GuideProfile, Language, TouristProfile, User, UserPreferences


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'is_guide_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_guide_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'passport_number', 'citizenship_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GuideProfile)
class GuideProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'availability', 'daily_rate_npr', 'created_at')
    list_filter = ('availability', 'languages')
    search_fields = ('user__username', 'license_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TouristProfile)
class TouristProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'emergency_contact_name', 'emergency_contact_phone', 'created_at')
    search_fields = ('user__username', 'emergency_contact_phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'currency', 'theme', 'push_notifications')
    list_filter = ('language', 'currency', 'theme', 'push_notifications')
