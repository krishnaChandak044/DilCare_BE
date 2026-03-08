"""
Core — Reusable DRF permissions.
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: only the object owner can access it.
    Expects the model to have a `user` ForeignKey field.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
