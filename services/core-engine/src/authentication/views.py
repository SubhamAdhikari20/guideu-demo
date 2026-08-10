from __future__ import annotations

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import EmailTokenObtainPairSerializer, UserSerializer


class RegistrationAPIView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "register"

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

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
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action in ('retrieve', 'update', 'partial_update'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Issues JWT access/refresh tokens from an email + password.

    Rate-limited per IP so the login endpoint can't be brute-forced.
    """

    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"
