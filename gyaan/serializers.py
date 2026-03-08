"""
Gyaan — Serializers.
"""
from rest_framework import serializers
from .models import WellnessTip, TipInteraction


class WellnessTipSerializer(serializers.ModelSerializer):
    """
    Includes per-user `completed` and `favorite` flags.
    These are injected from the TipInteraction table.
    """
    completed = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()

    class Meta:
        model = WellnessTip
        fields = [
            "id", "title", "description", "content",
            "category", "icon", "duration",
            "completed", "favorite", "created_at",
        ]

    def _get_interaction(self, obj):
        user = self.context.get("user")
        if not user:
            return None
        # Cache interactions per serializer instance to avoid N+1
        cache = getattr(self, "_interaction_cache", None)
        if cache is None:
            qs = TipInteraction.objects.filter(user=user)
            self._interaction_cache = {i.tip_id: i for i in qs}
            cache = self._interaction_cache
        return cache.get(obj.id)

    def get_completed(self, obj) -> bool:
        i = self._get_interaction(obj)
        return i.completed if i else False

    def get_favorite(self, obj) -> bool:
        i = self._get_interaction(obj)
        return i.favorite if i else False
