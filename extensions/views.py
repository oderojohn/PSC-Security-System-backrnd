from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import PhoneExtension, ReportedIssue, SecurityKey, KeyHistory
from .serializers import (
    PhoneExtensionSerializer,
    ReportedIssueSerializer,
    SecurityKeySerializer,
    KeyCheckoutSerializer,
    KeyReturnSerializer,
    KeyHistorySerializer
)

# Phone Extension Views
class PhoneExtensionListCreateView(generics.ListCreateAPIView):
    queryset = PhoneExtension.objects.all()
    serializer_class = PhoneExtensionSerializer

class PhoneExtensionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PhoneExtension.objects.all()
    serializer_class = PhoneExtensionSerializer

# Reported Issue Views
class ReportedIssueListCreateView(generics.ListCreateAPIView):
    queryset = ReportedIssue.objects.all()
    serializer_class = ReportedIssueSerializer

class ReportedIssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReportedIssue.objects.all()
    serializer_class = ReportedIssueSerializer

class UpdateIssueStatusView(generics.UpdateAPIView):
    queryset = ReportedIssue.objects.all()
    serializer_class = ReportedIssueSerializer
    lookup_field = 'pk'

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if 'status' not in request.data:
            return Response({'error': 'Status field is required'}, status=status.HTTP_400_BAD_REQUEST)
        valid_statuses = dict(ReportedIssue.STATUS_CHOICES).keys()
        if request.data['status'] not in valid_statuses:
            return Response({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, status=status.HTTP_400_BAD_REQUEST)
        instance.status = request.data['status']
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# Security Key Views
class SecurityKeyListView(generics.ListCreateAPIView):
    queryset = SecurityKey.objects.all()
    serializer_class = SecurityKeySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(key_id__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(current_holder_name__icontains=search_query)
            )
        return queryset

class SecurityKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SecurityKey.objects.all()
    serializer_class = SecurityKeySerializer

class SecurityKeyHistoryView(generics.ListAPIView):
    serializer_class = KeyHistorySerializer

    def get_queryset(self):
        return KeyHistory.objects.filter(key_id=self.kwargs['pk']).order_by('-timestamp')

class CheckoutKeyView(generics.UpdateAPIView):
    queryset = SecurityKey.objects.all()
    serializer_class = SecurityKeySerializer

    def update(self, request, *args, **kwargs):
        key = self.get_object()
        if key.status != 'available':
            return Response({'error': 'Key is not available for checkout'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = KeyCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key.status = 'checked-out'
        key.current_holder_name = serializer.validated_data['holder_name']
        key.current_holder_type = serializer.validated_data['holder_type']
        key.current_holder_phone = serializer.validated_data.get('holder_phone', '')
        key.checkout_time = timezone.now()
        key.save()

        KeyHistory.objects.create(
            key=key,
            action='checkout',
            holder_name=serializer.validated_data['holder_name'],
            holder_type=serializer.validated_data['holder_type'],
            holder_phone=serializer.validated_data.get('holder_phone', ''),
            user=request.user if request.user.is_authenticated else None,
            notes=serializer.validated_data.get('notes', '')
        )

        return Response(self.get_serializer(key).data)

class ReturnKeyView(generics.UpdateAPIView):
    queryset = SecurityKey.objects.all()
    serializer_class = SecurityKeySerializer

    def update(self, request, *args, **kwargs):
        key = self.get_object()
        if key.status != 'checked-out':
            return Response({'error': 'Key is not checked out'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = KeyReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        KeyHistory.objects.create(
            key=key,
            action='return',
            holder_name=key.current_holder_name,
            holder_type=key.current_holder_type,
            holder_phone=key.current_holder_phone,
            user=request.user if request.user.is_authenticated else None,
            notes=serializer.validated_data.get('notes', '')
        )

        key.status = 'available'
        key.return_time = timezone.now()
        key.current_holder_name = None
        key.current_holder_type = None
        key.current_holder_phone = None
        key.save()

        return Response(self.get_serializer(key).data)
