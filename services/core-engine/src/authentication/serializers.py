from __future__ import annotations

from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import GuideProfile, Language, TouristProfile, User, UserPreferences


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'name')


class GuideProfileSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = GuideProfile
        fields = (
            'id', 'user', 'license_number', 'verification_documents', 'bio', 'languages',
            'service_areas', 'availability', 'current_latitude', 'current_longitude',
            'hourly_rate_npr', 'daily_rate_npr', 'availability_updated_at',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')


class TouristProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TouristProfile
        fields = ('id', 'user', 'emergency_contact_name', 'emergency_contact_phone', 'citizenship_document', 'passport_expiry_date', 'created_at', 'updated_at')
        read_only_fields = ('user', 'availability_updated_at', 'created_at', 'updated_at')


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = (
            'language', 'currency', 'theme', 'push_notifications', 'email_notifications',
            'booking_notifications', 'festival_notifications', 'safety_notifications',
            'profile_is_private', 'updated_at'
        )
        read_only_fields = ('updated_at',)


class UserSerializer(serializers.ModelSerializer):
    guide_profile = GuideProfileSerializer(read_only=True)
    tourist_profile = TouristProfileSerializer(read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone_number',
            'nationality', 'passport_number', 'citizenship_number', 'date_of_birth', 'is_guide_verified',
            'is_active', 'is_staff',
            'guide_profile', 'tourist_profile', 'preferences', 'created_at', 'updated_at'
        )
        read_only_fields = ('role', 'is_guide_verified', 'is_active', 'is_staff', 'created_at', 'updated_at')

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegistrationSerializer(serializers.ModelSerializer):
    """Public registration. Administrators can never be created from this route."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(
        choices=(User.Roles.TOURIST, User.Roles.GUIDE), required=False, default=User.Roles.TOURIST
    )
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    service_areas = serializers.ListField(
        child=serializers.CharField(max_length=80), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'first_name', 'last_name', 'role',
            'phone_number', 'nationality', 'license_number', 'bio', 'service_areas'
        )
        read_only_fields = ('id',)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get('role') == User.Roles.GUIDE and not attrs.get('license_number', '').strip():
            raise serializers.ValidationError({'license_number': 'A guide licence number is required.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        profile_data = {
            key: validated_data.pop(key, None) for key in ('license_number', 'bio', 'service_areas')
        }
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        if user.role == User.Roles.GUIDE:
            profile = user.guide_profile
            for key, value in profile_data.items():
                if value is not None:
                    setattr(profile, key, value)
            profile.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class EmailTokenObtainPairSerializer(serializers.Serializer):
    """Log in with email + password — the mobile login screen uses email, but
    the default SimpleJWT serializer expects the username field."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        from rest_framework_simplejwt.tokens import RefreshToken

        try:
            user = User.objects.get(email__iexact=attrs['email'])
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Invalid email or password.') from exc

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is disabled.')

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['email'] = user.email
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        }
