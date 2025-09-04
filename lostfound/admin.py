from django.contrib import admin
from .models import LostItem, FoundItem, PickupLog, SystemSettings, EmailLog

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ('type', 'item_name', 'card_last_four', 'owner_name', 'place_lost', 'status', 'photo')
    list_filter = ('type', 'status')
    search_fields = ('item_name', 'card_last_four', 'owner_name')

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('type', 'item_name', 'card_last_four', 'owner_name', 'place_found', 'status','photo')
    list_filter = ('type', 'status')
    search_fields = ('item_name', 'card_last_four', 'owner_name')

@admin.register(PickupLog)
class PickupLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'picked_by_name', 'picked_by_member_id', 'pickup_date')
    search_fields = ('picked_by_name', 'picked_by_member_id')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email_type', 'recipient', 'lost_item', 'sent_at', 'subject')
    list_filter = ('email_type', 'sent_at')
    search_fields = ('recipient', 'subject')
    readonly_fields = ('sent_at',)

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')
    list_editable = ('value',)