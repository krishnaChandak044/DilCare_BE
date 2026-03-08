"""
Core — View mixins for DRY queryset filtering.
"""


class OwnerQuerySetMixin:
    """
    Automatically filter querysets to only include objects
    belonging to the requesting user.
    Expects the model to have a `user` ForeignKey field.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
