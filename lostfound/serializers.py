from rest_framework import serializers
from .models import LostItem, FoundItem, PickupLog

class LostItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostItem
        fields = '__all__'
        read_only_fields = ('date_reported', 'last_updated', 'status', 'reported_by')

class FoundItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundItem
        fields = '__all__'
        read_only_fields = ('date_reported', 'last_updated', 'reported_by')

class PickupLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupLog
        fields = '__all__'
        read_only_fields = ('pickup_date', 'verified_by')

class ItemStatsSerializer(serializers.Serializer):
    lost_count = serializers.IntegerField()
    found_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()