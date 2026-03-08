"""
DilCare Backend — Root URL configuration
All API routes are namespaced under /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── API v1 ──────────────────────────────────────────────
    path("api/v1/auth/", include("accounts.urls.auth_urls")),
    path("api/v1/user/", include("accounts.urls.user_urls")),
    path("api/v1/health/", include("health.urls")),
    path("api/v1/medicine/", include("medicine.urls")),
    path("api/v1/water/", include("water.urls")),
    path("api/v1/family/", include("family.urls")),
    path("api/v1/doctor/", include("doctor.urls")),
    path("api/v1/steps/", include("steps.urls")),
    path("api/v1/community/", include("community.urls")),
    # ── API Docs ────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
