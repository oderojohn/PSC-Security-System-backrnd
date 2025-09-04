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

    def validate_recipient_phone(self, value):
        if value and (not value.isdigit() or len(value) < 10):
            raise serializers.ValidationError("Enter a valid recipient phone number (at least 10 digits).")
        return value

    def validate_dropper_phone(self, value):
        if value and (not value.isdigit() or len(value) < 10):
            raise serializers.ValidationError("Enter a valid dropper phone number (at least 10 digits).")
        return value

    def validate_recipient_id(self, value):
        if value and len(value) > 6:
            raise serializers.ValidationError("Recipient ID cannot exceed 6 characters.")
        return value

    def validate_dropper_id(self, value):
        if value and len(value) > 6:
            raise serializers.ValidationError("Member number cannot exceed 6 characters.")
        return value

    def validate(self, data):
        # Ensure either dropper_phone OR dropper_id is provided
        dropper_phone = data.get('dropper_phone')
        dropper_id = data.get('dropper_id')

        if not dropper_phone and not dropper_id:
            raise serializers.ValidationError("Either dropper phone number or member number must be provided.")

        # Ensure either recipient_phone OR recipient_id is provided
        recipient_phone = data.get('recipient_phone')
        recipient_id = data.get('recipient_id')

        if not recipient_phone and not recipient_id:
            raise serializers.ValidationError("Either recipient phone number or recipient ID must be provided.")

        # Ensure description is provided
        if not data.get('description'):
            raise serializers.ValidationError("Description is required.")

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Hide shelf for non-pending or if it's a key
        if instance.status != Package.PENDING or instance.type == Package.KEYS:
            data['shelf'] = None
        return data


class PickPackageSerializer(serializers.ModelSerializer):
    picker_id = serializers.CharField(required=False, allow_blank=True )
    picked_by = serializers.CharField(required=False, allow_blank=True )
    picker_phone = serializers.CharField(required=False, allow_blank=True )

    class Meta:
        model = Package
        fields = ['picked_by', 'picker_phone', 'picker_id', 'shelf']
        read_only_fields = ('shelf',)

    def validate_picker_phone(self, value):
        if value and (not value.isdigit() or len(value) < 10):
            raise serializers.ValidationError("Enter a valid picker phone number (at least 10 digits).")
        return value

    def validate_picker_id(self, value):
        if value and len(value) > 6:
            raise serializers.ValidationError("Member number cannot exceed 6 characters.")
        return value

    def validate(self, data):
        # Ensure at least one field is provided
        picked_by = data.get('picked_by')
        picker_phone = data.get('picker_phone')
        picker_id = data.get('picker_id')

        if not picked_by and not picker_phone and not picker_id:
            raise serializers.ValidationError("At least one field (name, phone, or member number) must be provided.")

        return data

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