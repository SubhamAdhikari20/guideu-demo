from __future__ import annotations

from rest_framework import permissions, viewsets

from .models import TrekkingPermit
from .serializers import TrekkingPermitSerializer


class TrekkingPermitViewSet(viewsets.ModelViewSet):
    queryset = TrekkingPermit.objects.all().order_by('-created_at')
    serializer_class = TrekkingPermitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if self.request.user.is_staff else qs.filter(applicant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    def update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Permit decisions are managed by administrators.')
        return super().update(request, *args, **kwargs)
