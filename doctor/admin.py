"""
Doctor — Admin configuration
"""
from django.contrib import admin
from .models import Doctor, Appointment, MedicalDocument


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'user', 'phone', 'hospital', 'is_primary', 'created_at')
    list_filter = ('specialty', 'is_primary', 'created_at')
    search_fields = ('name', 'user__email', 'phone', 'hospital')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'specialty', 'is_primary')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'hospital', 'address')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'user', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('doctor_name', 'user__email', 'reason', 'location')
    raw_id_fields = ('user', 'doctor')
    readonly_fields = ('created_at', 'updated_at', 'doctor_name', 'specialty')
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Appointment Details', {
            'fields': ('user', 'doctor', 'doctor_name', 'specialty', 'appointment_date', 'appointment_time')
        }),
        ('Additional Info', {
            'fields': ('reason', 'location', 'status', 'notes')
        }),
        ('System', {
            'fields': ('reminder_sent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'user', 'document_date', 'doctor', 'created_at')
    list_filter = ('document_type', 'document_date', 'created_at')
    search_fields = ('title', 'user__email', 'notes')
    raw_id_fields = ('user', 'doctor', 'appointment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'document_date'
    fieldsets = (
        ('Document Info', {
            'fields': ('user', 'title', 'document_type', 'document_date')
        }),
        ('Related Records', {
            'fields': ('doctor', 'appointment')
        }),
        ('Files', {
            'fields': ('file', 'file_url')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

