from __future__ import annotations

from django.db.models import F, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from src.common.permissions import IsOwnerOrReadOnly

from .models import Review
from .serializers import ModerateSerializer, ReviewSerializer, ReviewSummarySerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Tourists review guides/routes. Public reads show approved reviews only."""

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    owner_field = "author"
    filterset_fields = ("guide", "route", "rating")
    ordering_fields = ("created_at", "rating", "helpful_count")
    search_fields = ("title", "comment")

    def get_queryset(self):
        user = self.request.user
        qs = Review.objects.select_related("author")
        if user.is_authenticated and user.is_staff:
            return qs
        if user.is_authenticated:
            # Own reviews (any status) plus everyone's approved reviews.
            return qs.filter(Q(status=Review.Status.APPROVED) | Q(author=user))
        return qs.approved()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request, *args, **kwargs):
        """Aggregate rating for ?guide=<id> or ?route=<id>."""
        qs = Review.objects.all()
        if "guide" in request.query_params:
            qs = qs.filter(guide_id=request.query_params["guide"])
        elif "route" in request.query_params:
            qs = qs.filter(route_id=request.query_params["route"])
        return Response(ReviewSummarySerializer(qs.summary()).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def moderate(self, request, pk=None, *args, **kwargs):
        """Admin approves/rejects a review (moderation + abuse handling)."""
        review = self.get_object()
        serializer = ModerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review.status = serializer.validated_data["status"]
        review.save(update_fields=["status", "updated_at"])
        return Response(ReviewSerializer(review).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None, *args, **kwargs):
        """Mark a review as helpful (upvote)."""
        review = self.get_object()
        Review.objects.filter(pk=review.pk).update(helpful_count=F("helpful_count") + 1)
        review.refresh_from_db(fields=["helpful_count"])
        return Response({"helpful_count": review.helpful_count})
