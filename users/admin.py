# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import EventLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('phone', 'department')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'phone', 'department', 'password1', 'password2')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('username',)

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'object_type', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__username', 'ip_address', 'object_type', 'object_id')
    readonly_fields = ('timestamp',)  # Make timestamp non-editable
    date_hierarchy = 'timestamp'  # Add date-based navigation
    ordering = ('-timestamp',)  # Show newest first
    
    # Customize how fields are displayed in detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'action', 'timestamp')
        }),
        ('Object Information', {
            'fields': ('object_type', 'object_id')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)  # Makes this section collapsible
        })
    )
    
    # Add a custom action to export logs
    actions = ['export_as_json']
    
    def export_as_json(self, request, queryset):
        """Admin action to export selected logs as JSON"""
        from django.http import JsonResponse
        import json
        data = []
        for log in queryset:
            data.append({
                'user': str(log.user),
                'action': log.get_action_display(),
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address,
                'object': f"{log.object_type} ({log.object_id})" if log.object_type else None,
                'metadata': log.metadata
            })
        return JsonResponse(data, safe=False)
    export_as_json.short_description = "Export selected logs as JSON"