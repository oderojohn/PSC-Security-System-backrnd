from rest_framework import serializers
from .models import LostItem, FoundItem, PickupLog, SystemSettings
import re

class DailyCountSerializer(serializers.Serializer):
    day = serializers.DateTimeField()
    count = serializers.IntegerField()

class LostItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostItem
        fields = '__all__'
        read_only_fields = ('date_reported', 'last_updated', 'status', 'reported_by', 'tracking_id')

    def validate_reporter_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value

    def validate_card_last_four(self, value):
        if value:
            # Pattern: Letter + exactly 4 digits, or Letter + exactly 4 digits + letter
            pattern = r'^[A-Z][0-9]{4}[A-Z]?$'
            if not re.match(pattern, value.upper()):
                raise serializers.ValidationError(
                    "Card last four must start with a letter (A-Z), followed by exactly 4 digits, "
                    "and optionally end with a letter. Examples: A1234, A1234B"
                )
        return value

    def validate(self, data):
        if data.get('type') == 'card' and not data.get('card_last_four'):
            raise serializers.ValidationError("Card last four digits are required for card type")
        if data.get('type') == 'item' and not data.get('item_name'):
            raise serializers.ValidationError("Item name is required for item type")
        return data

class FoundItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundItem
        fields = '__all__'
        read_only_fields = ('date_reported', 'last_updated', 'reported_by')

    def validate_card_last_four(self, value):
        if value:
            # Pattern: Letter + exactly 4 digits, or Letter + exactly 4 digits + letter
            pattern = r'^[A-Z][0-9]{4}[A-Z]?$'
            if not re.match(pattern, value.upper()):
                raise serializers.ValidationError(
                    "Card last four must start with a letter (A-Z), followed by exactly 4 digits, "
                    "and optionally end with a letter. Examples: A1234, A1234B"
                )
        return value

    def validate(self, data):
        if data.get('type') == 'card' and not data.get('card_last_four'):
            raise serializers.ValidationError("Card last four digits are required for card type")
        if data.get('type') == 'item' and not data.get('item_name'):
            raise serializers.ValidationError("Item name is required for item type")
        return data

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

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'
        read_only_fields = ('updated_at',)
