# views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Package
from .serializers import PackageSerializer, PickPackageSerializer
from .printer_service import PackagePrinter
from threading import Thread
import logging
from users.permissions import IsAdmin, IsStaff, IsReception
import csv
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'code', 'description', 'recipient_name', 'recipient_phone',
        'dropped_by', 'picked_by', 'shelf'
    ]
    filterset_fields = ['status', 'type', 'shelf']

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        time_range = self.request.query_params.get('time_range', None)

        if status_param == 'pending':
            queryset = queryset.filter(status=Package.PENDING)
        elif status_param == 'picked':
            queryset = queryset.filter(status=Package.PICKED)

        if time_range == 'today':
            today = datetime.now().date()
            queryset = queryset.filter(created_at__date=today)
        elif time_range == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif time_range == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'], serializer_class=PickPackageSerializer)
    def pick(self, request, pk=None):
        package = self.get_object()
        if package.status == Package.PICKED:
            return Response(
                {'error': 'Package already picked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PickPackageSerializer(package, data=request.data)
        if serializer.is_valid():
            package = serializer.save()
            package.status = Package.PICKED
            package.picked_at = timezone.now()
            package.shelf = None
            package.save()
            
            response_data = serializer.data
            response_data['shelf'] = None
            return Response(
            response_data,
            status=status.HTTP_200_OK
        )
            return Response(PackageSerializer(package).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        pending_count = Package.objects.filter(status=Package.PENDING).count()
        picked_count = Package.objects.filter(status=Package.PICKED).count()
        total_count = Package.objects.count()
        shelves_occupied = Package.objects.filter(status=Package.PENDING).values('shelf').distinct().count()

        return Response({
            'pending': pending_count,
            'picked': picked_count,
            'total': total_count,
            'shelves_occupied': shelves_occupied
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="packages_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Type', 'Description', 'Recipient Name', 'Recipient Phone',
            'Dropped By', 'Dropper Phone', 'Picked By', 'Picker Phone',
            'Shelf', 'Status', 'Created At', 'Updated At'
        ])

        for package in queryset:
            writer.writerow([
                package.code,
                package.get_type_display(),
                package.description,
                package.recipient_name,
                package.recipient_phone,
                package.dropped_by,
                package.dropper_phone,
                package.picked_by,
                package.picker_phone,
                package.shelf,
                package.get_status_display(),
                package.created_at,
                package.updated_at
            ])

        return response

    @action(detail=False, methods=['get'])
    def summary(self, request):
        daily_summary = Package.objects.values('created_at__date').annotate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=Package.PENDING)),
            picked=Count('id', filter=Q(status=Package.PICKED))
        ).order_by('created_at__date')

        type_distribution = Package.objects.values('type').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'daily_summary': list(daily_summary),
            'type_distribution': list(type_distribution)
        })

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin | IsReception | IsStaff]
        elif self.action in ['pick']:
            permission_classes = [IsStaff | IsReception]
        elif self.action in ['export']:
            permission_classes = [IsAdmin | IsStaff]
        else:
            permission_classes = [IsStaff]
        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            serializer = PackageSerializer(data=request.data)
            if serializer.is_valid():
                package = serializer.save()

                print_data = {
                    'code': package.code,
                    'type': package.get_type_display(),
                    'description': package.description,
                    'recipient_name': package.recipient_name,
                    'recipient_phone': package.recipient_phone,
                    'dropped_by': package.dropped_by,
                    'dropper_phone': package.dropper_phone,
                    'shelf': package.shelf
                }

                print_thread = Thread(
                    target=self._print_receipt,
                    args=(print_data,),
                    daemon=True
                )
                print_thread.start()

                return Response(PackageSerializer(package).data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("Error creating package")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _print_receipt(self, package_data):
        printer = PackagePrinter()
        if not printer.print_package_receipt(package_data):
            logger.error(f"Failed to print receipt for package {package_data['code']}")
