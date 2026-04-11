"""
Medicine — URL routing for medicine and prescription endpoints.
"""
from django.urls import path
from . import views

app_name = "medicine"

urlpatterns = [
    # Medicines CRUD
    path("medicines/", views.MedicineListCreateView.as_view(), name="medicine-list-create"),
    path("medicines/<uuid:pk>/", views.MedicineDetailView.as_view(), name="medicine-detail"),

    # Inventory update (PATCH only)
    path("medicines/<uuid:pk>/inventory/", views.MedicineInventoryUpdateView.as_view(), name="medicine-inventory-update"),

    # Today's schedule (flat list with intake status + inventory)
    path("today/", views.TodayMedicinesView.as_view(), name="today-medicines"),

    # Intake management
    path("intakes/", views.MedicineIntakeListView.as_view(), name="intake-list"),
    path("intakes/<uuid:intake_id>/toggle/", views.MedicineIntakeToggleView.as_view(), name="intake-toggle"),

    # Summary/Stats
    path("summary/", views.MedicineSummaryView.as_view(), name="medicine-summary"),

    # Running-out list
    path("running-out/", views.RunningOutMedicinesView.as_view(), name="running-out"),

    # Prescriptions CRUD
    path("prescriptions/", views.PrescriptionListCreateView.as_view(), name="prescription-list-create"),
    path("prescriptions/<uuid:pk>/", views.PrescriptionDetailView.as_view(), name="prescription-detail"),
]
