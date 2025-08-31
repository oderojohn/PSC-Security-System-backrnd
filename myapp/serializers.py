from rest_framework import serializers
from .models import Package, AppSettings
from django.utils import timezone


class PackageSerializer(serializers.ModelSerializer):
    
    package_type = serializers.SerializerMethodField()


    class Meta:
        model = Package
        fields = '__all__'
        read_only_fields = ('code', 'created_at', 'updated_at', 'shelf', 'picked_at')

    def get_package_type(self, obj):
        return obj.get_type_display()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Hide shelf for non-pending or if it's a key
        if instance.status != Package.PENDING or instance.type == Package.KEYS:
            data['shelf'] = None
        return data


class PickPackageSerializer(serializers.ModelSerializer):
    picker_id = serializers.CharField(required=True)
    picked_by = serializers.CharField(required=True)
    picker_phone = serializers.CharField(required=True)

    class Meta:
        model = Package
        fields = ['picked_by', 'picker_phone', 'picker_id', 'shelf']
        read_only_fields = ('shelf',)

    def validate_picker_phone(self, value):
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_picker_id(self, value):
        if not isinstance(value, str) or not value.strip():
            raise serializers.ValidationError("Picker ID must be a non-empty string.")
        return value

    def update(self, instance, validated_data):
        instance.picked_by = validated_data.get('picked_by', instance.picked_by)
        instance.picker_phone = validated_data.get('picker_phone', instance.picker_phone)
        instance.picker_id = validated_data.get('picker_id', instance.picker_id)
        instance.picked_at = timezone.now()
        instance.status = Package.PICKED

        if instance.type != Package.KEYS:
            instance.shelf = None

        instance.save()
        return instance


class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        # Ensure only one instance
        if AppSettings.objects.exists():
            raise serializers.ValidationError("Settings already exist. Use update instead.")
        return super().create(validated_data)