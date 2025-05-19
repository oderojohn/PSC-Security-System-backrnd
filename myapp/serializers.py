from rest_framework import serializers
from .models import Package

class PackageSerializer(serializers.ModelSerializer):
    package_type = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = '__all__'
        read_only_fields = ('code', 'created_at', 'updated_at', 'shelf')

    def get_package_type(self, obj):
        return obj.get_type_display()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Hide shelf for non-pending or if it's a key
        if instance.status != Package.PENDING or instance.type == Package.KEYS:
            data['shelf'] = None
        return data


class PickPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['picked_by', 'picker_phone', 'shelf']
        read_only_fields = ('shelf',)

    def update(self, instance, validated_data):
        instance.picked_by = validated_data.get('picked_by', instance.picked_by)
        instance.picker_phone = validated_data.get('picker_phone', instance.picker_phone)
        instance.status = Package.PICKED

        # Only clear shelf for non-key types
        if instance.type != Package.KEYS:
            instance.shelf = None

        instance.save()
        return instance
