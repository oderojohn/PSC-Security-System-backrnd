from rest_framework import serializers
from .models import LostItem, FoundItem, PickupLog

class DailyCountSerializer(serializers.Serializer):
    day = serializers.DateTimeField()
    count = serializers.IntegerField()

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
class ItemTypeCountSerializer(serializers.Serializer):
    type = serializers.CharField()
    count = serializers.IntegerField()
class WeeklyReportSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    lost_items_total = serializers.IntegerField()
    lost_items_by_type = ItemTypeCountSerializer(many=True)
    found_items_total = serializers.IntegerField()
    found_items_by_type = ItemTypeCountSerializer(many=True)
    claimed_items_count = serializers.IntegerField()
    claim_rate = serializers.FloatField()

    lost_items_daily = DailyCountSerializer(many=True)
    found_items_daily = DailyCountSerializer(many=True)
