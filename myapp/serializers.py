from rest_framework import serializers
from .models import Package

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'
        read_only_fields = ('code', 'created_at', 'updated_at', 'shelf')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Include shelf only for pending packages
        if instance.status != Package.PENDING:
            data['shelf'] = None
        return data

class PickPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['picked_by', 'picker_phone', 'shelf']
        read_only_fields = ('shelf',)