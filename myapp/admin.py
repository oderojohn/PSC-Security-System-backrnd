from django.contrib import admin
from .models import Package, AppSettings, PackageHistory

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


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ('printer_ip', 'printer_port', 'enable_qr_codes', 'auto_print_on_create', 'updated_at')
    fieldsets = (
        ('Printer Settings', {
            'fields': ('printer_ip', 'printer_port')
        }),
        ('Features', {
            'fields': ('enable_qr_codes', 'auto_print_on_create', 'enable_reprint', 'max_reprint_attempts')
        }),
        ('Notifications', {
            'fields': ('notification_email', 'enable_sms_notifications', 'sms_api_key')
        }),
        ('Defaults', {
            'fields': ('default_package_type',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        # Prevent adding more than one settings instance
        return not AppSettings.objects.exists()

    def add_view(self, request, form_url='', extra_context=None):
        # If settings already exist, redirect to change view
        if AppSettings.objects.exists():
            settings = AppSettings.objects.first()
            from django.shortcuts import redirect
            return redirect('admin:myapp_appsettings_change', settings.pk)
        return super().add_view(request, form_url, extra_context)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings instance
        return False


@admin.register(PackageHistory)
class PackageHistoryAdmin(admin.ModelAdmin):
    list_display = ('package', 'action', 'old_status', 'new_status', 'performed_by', 'timestamp')
    list_filter = ('action', 'old_status', 'new_status', 'timestamp')
    search_fields = ('package__code', 'performed_by', 'notes')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)