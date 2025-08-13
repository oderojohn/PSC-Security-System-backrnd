from django.contrib import admin
from .models import LostItem, FoundItem, PickupLog

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ('type', 'item_name', 'card_last_four', 'owner_name', 'place_lost', 'status')
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