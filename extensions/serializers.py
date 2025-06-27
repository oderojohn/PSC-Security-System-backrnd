from rest_framework import serializers
from .models import PhoneExtension, ReportedIssue, KeyHistory, SecurityKey

class PhoneExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneExtension
        fields = '__all__'

class ReportedIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportedIssue
        fields = '__all__'
        read_only_fields = ('created_at',)

class KeyCheckoutSerializer(serializers.Serializer):
    holder_name = serializers.CharField(max_length=100, required=True)
    holder_type = serializers.ChoiceField(choices=SecurityKey.HOLDER_TYPES, required=True)
    holder_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

class KeyReturnSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

class KeyHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyHistory
        fields = '__all__'

class SecurityKeySerializer(serializers.ModelSerializer):
    history = KeyHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = SecurityKey
        fields = '__all__'
        read_only_fields = ('checkout_time', 'return_time')

