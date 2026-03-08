"""
Gyaan — API views for wellness tips.
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import WellnessTip, TipInteraction
from .serializers import WellnessTipSerializer


class TipListView(generics.ListAPIView):
    """
    GET /api/v1/gyaan/tips/
    Optional query param: ?category=nutrition|exercise|meditation|ayurveda
    Returns tips with per-user completed/favorite flags.
    """
    serializer_class = WellnessTipSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="category", type=str, required=False),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = WellnessTip.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx


class TipDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/gyaan/tips/{id}/
    """
    serializer_class = WellnessTipSerializer
    permission_classes = [IsAuthenticated]
    queryset = WellnessTip.objects.filter(is_active=True)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx


class ToggleFavoriteView(APIView):
    """
    POST /api/v1/gyaan/tips/{id}/favorite/
    Toggles the favourite status for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def post(self, request, pk):
        try:
            tip = WellnessTip.objects.get(pk=pk, is_active=True)
        except WellnessTip.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        interaction, _ = TipInteraction.objects.get_or_create(user=request.user, tip=tip)
        interaction.favorite = not interaction.favorite
        interaction.favorited_at = timezone.now() if interaction.favorite else None
        interaction.save(update_fields=["favorite", "favorited_at"])
        return Response({"favorite": interaction.favorite})


class MarkCompleteView(APIView):
    """
    POST /api/v1/gyaan/tips/{id}/complete/
    Toggles the completed status for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def post(self, request, pk):
        try:
            tip = WellnessTip.objects.get(pk=pk, is_active=True)
        except WellnessTip.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        interaction, _ = TipInteraction.objects.get_or_create(user=request.user, tip=tip)
        interaction.completed = not interaction.completed
        interaction.completed_at = timezone.now() if interaction.completed else None
        interaction.save(update_fields=["completed", "completed_at"])
        return Response({"completed": interaction.completed})


class TipStatsView(APIView):
    """
    GET /api/v1/gyaan/stats/
    Returns total tips, completed count, favorite count.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        total = WellnessTip.objects.filter(is_active=True).count()
        interactions = TipInteraction.objects.filter(user=request.user)
        completed = interactions.filter(completed=True).count()
        favorites = interactions.filter(favorite=True).count()
        return Response({
            "total_tips": total,
            "completed": completed,
            "favorites": favorites,
            "progress": round(completed / total * 100, 1) if total else 0,
        })

