from __future__ import annotations

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import GuideProfile, User, UserPreferences
from .serializers import (
    ChangePasswordSerializer,
    EmailTokenObtainPairSerializer,
    GuideProfileSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
    UserPreferencesSerializer,
    UserSerializer,
)


class RegistrationAPIView(APIView):
    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "register"

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    filterset_fields = ('role', 'is_active', 'is_guide_verified')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering_fields = ('created_at', 'email', 'role')

    # The standard CRUD routes; anything else on this viewset comes from an
    # @action decorator that declares its own permissions.
    CRUD_ACTIONS = ('create', 'list', 'retrieve', 'update', 'partial_update', 'destroy')

    def get_permissions(self):
        """Per-action permissions for the built-in routes.

        Routes added with ``@action`` carry their own ``permission_classes``,
        which DRF has already applied to this instance. Falling through to the
        admin-only default below would silently override them — that is what made
        ``/users/me/`` return 403 for the signed-in user it exists to serve.
        """
        if self.action not in self.CRUD_ACTIONS:
            return super().get_permissions()
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if self.request.user.is_staff else qs.filter(pk=self.request.user.pk)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        if request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def preferences(self, request, *args, **kwargs):
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        if request.method == 'PATCH':
            serializer = UserPreferencesSerializer(
                preferences, data=request.data, partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = UserPreferencesSerializer(preferences, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='verify-guide', permission_classes=[permissions.IsAdminUser])
    def verify_guide(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        if user.role != User.Roles.GUIDE:
            return Response({'detail': 'The selected account is not a guide.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_guide_verified = bool(request.data.get('verified', True))
        user.save(update_fields=['is_guide_verified', 'updated_at'])
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def suspend(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response({'detail': 'You cannot suspend your own administrator account.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = bool(request.data.get('active', False))
        user.save(update_fields=['is_active', 'updated_at'])
        return Response({'detail': 'Account activated.' if user.is_active else 'Account suspended.'})

    @action(detail=False, methods=['post'], url_path='change-password', permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response({'current_password': ['The current password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password', 'updated_at'])
        return Response({'detail': 'Password changed successfully.'})

    @action(detail=False, methods=['get', 'patch'], url_path='guide-profile', permission_classes=[permissions.IsAuthenticated])
    def guide_profile(self, request, *args, **kwargs):
        if request.user.role != User.Roles.GUIDE:
            return Response({'detail': 'Only guide accounts have a guide profile.'}, status=status.HTTP_403_FORBIDDEN)
        profile = request.user.guide_profile
        if request.method == 'PATCH':
            serializer = GuideProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            if any(key in request.data for key in ('availability', 'current_latitude', 'current_longitude')):
                from django.utils import timezone
                serializer.save(availability_updated_at=timezone.now())
            else:
                serializer.save()
        else:
            serializer = GuideProfileSerializer(profile)
        return Response(serializer.data)


class PasswordResetRequestAPIView(APIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data['email'], is_active=True).first()
        response = {'detail': 'If the account exists, password reset instructions have been sent.'}
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                'Reset your GuideU password',
                f'Use this reset code in GuideU. Account: {uid}\nCode: {token}',
                None,
                [user.email],
                fail_silently=True,
            )
            if settings.DEBUG:
                response['debug_uid'] = uid
                response['debug_token'] = token
        return Response(response)


class PasswordResetConfirmAPIView(APIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if not user or not default_token_generator.check_token(user, serializer.validated_data['token']):
            return Response({'detail': 'The reset code is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password', 'updated_at'])
        return Response({'detail': 'Password reset successfully.'})


class EmailTokenObtainPairView(TokenObtainPairView):
    """Issues JWT access/refresh tokens from an email + password.

    Rate-limited per IP so the login endpoint can't be brute-forced.
    """

    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"
