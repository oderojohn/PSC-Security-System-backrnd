from django.contrib import admin
from .models import Package

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('code', 'type', 'recipient_name', 'status', 'shelf', 'created_at')
    list_filter = ('status', 'type', 'shelf')
    search_fields = ('code', 'recipient_name', 'description', 'shelf')
    readonly_fields = ('code', 'created_at', 'updated_at', 'shelf')
    fieldsets = (
        (None, {
            'fields': ('code', 'type', 'status', 'shelf')
        }),
        ('Package Details', {
            'fields': ('description', 'recipient_name', 'recipient_phone')
        }),
        ('Drop Information', {
            'fields': ('dropped_by', 'dropper_phone', 'created_at')
        }),
        ('Pick Information', {
            'fields': ('picked_by', 'picker_phone', 'picked_at', 'updated_at','picker_id'),
            'classes': ('collapse',)
        }),
    )