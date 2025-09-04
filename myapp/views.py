# views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Package, AppSettings, PackageHistory
from .serializers import PackageSerializer, PickPackageSerializer, AppSettingsSerializer
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
            queryset = queryset.filter(picked_at__date=today)
        elif time_range == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            queryset = queryset.filter(picked_at__gte=week_ago)
        elif time_range == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            queryset = queryset.filter(picked_at__gte=month_ago)

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
            old_status = package.status
            package = serializer.save()

            # Log history
            PackageHistory.objects.create(
                package=package,
                action='picked',
                old_status=old_status,
                new_status=Package.PICKED,
                performed_by=request.data.get('picked_by', ''),
                notes=f"Picked by {request.data.get('picked_by', '')} with ID {request.data.get('picker_id', '')}"
            )

            response_data = serializer.data
            response_data['shelf'] = None
            return Response(response_data, status=status.HTTP_200_OK)

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
        elif self.action in ['reprint']:
            permission_classes = [IsAdmin | IsReception | IsStaff]
        elif self.action in ['history']:
            permission_classes = [IsStaff]
        else:
            permission_classes = [IsStaff]
        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            serializer = PackageSerializer(data=request.data)
            if serializer.is_valid():
                package = serializer.save()

                # Log history
                dropper_info = request.data.get('dropped_by', 'Unknown')
                if request.data.get('dropper_id'):
                    dropper_info += f" (Member: {request.data.get('dropper_id')})"
                elif request.data.get('dropper_phone'):
                    dropper_info += f" (Phone: {request.data.get('dropper_phone')})"

                PackageHistory.objects.create(
                    package=package,
                    action='created',
                    new_status=Package.PENDING,
                    performed_by=getattr(request.user, 'username', 'System'),
                    notes=f"Package created by {dropper_info}"
                )

                settings = AppSettings.get_settings()
                if settings.auto_print_on_create:
                    print_data = {
                        'code': package.code,
                        'type': package.get_type_display(),
                        'description': package.description,
                        'recipient_name': package.recipient_name,
                        'recipient_phone': package.recipient_phone,
                        'recipient_id': package.recipient_id,
                        'dropped_by': package.dropped_by,
                        'dropper_phone': package.dropper_phone,
                        'dropper_id': package.dropper_id,
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

    def update(self, request, *args, **kwargs):
        """Override update to log package edits"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Store original values for comparison
        original_data = {
            'type': instance.type,
            'description': instance.description,
            'recipient_name': instance.recipient_name,
            'recipient_phone': instance.recipient_phone,
            'dropped_by': instance.dropped_by,
            'dropper_phone': instance.dropper_phone,
        }

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.error(f"Package update validation failed for package {instance.code}: {serializer.errors}")
            logger.error(f"Request data: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get updated data
        updated_data = serializer.validated_data
        changes = []

        # Compare fields and track changes
        for field in ['type', 'description', 'recipient_name', 'recipient_phone', 'dropped_by', 'dropper_phone']:
            if field in updated_data and updated_data[field] != original_data[field]:
                changes.append(f"{field}: '{original_data[field]}' → '{updated_data[field]}'")

        # Perform the update
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # Log the edit if there were changes
        if changes:
            PackageHistory.objects.create(
                package=instance,
                action='edited',
                performed_by=getattr(request.user, 'username', 'System'),
                notes=f"Package details updated: {', '.join(changes)}"
            )

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to log package edits"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def reprint(self, request, pk=None):
        package = self.get_object()
        settings = AppSettings.get_settings()

        if not settings.enable_reprint:
            return Response(
                {'error': 'Reprint functionality is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check max reprint attempts
        reprint_count = PackageHistory.objects.filter(
            package=package,
            action='reprinted'
        ).count()

        if reprint_count >= settings.max_reprint_attempts:
            return Response(
                {
                    'error': f'Maximum reprint attempts ({settings.max_reprint_attempts}) exceeded',
                    'current_attempts': reprint_count
                },
                status=status.HTTP_403_FORBIDDEN
            )

        print_data = {
            'code': package.code,
            'type': package.get_type_display(),
            'description': package.description,
            'recipient_name': package.recipient_name,
            'recipient_phone': package.recipient_phone,
            'recipient_id': package.recipient_id,
            'dropped_by': package.dropped_by,
            'dropper_phone': package.dropper_phone,
            'dropper_id': package.dropper_id,
            'shelf': package.shelf
        }

        # Check for recent edits
        recent_edit = PackageHistory.objects.filter(
            package=package,
            action='edited'
        ).order_by('-timestamp').first()

        edit_note = ""
        if recent_edit:
            edit_note = f" (after edit: {recent_edit.notes})"

        printer = PackagePrinter(ip=settings.printer_ip, port=settings.printer_port, enable_qr=settings.enable_qr_codes)
        if printer.print_label_receipt(print_data):
            # Log history
            PackageHistory.objects.create(
                package=package,
                action='reprinted',
                performed_by=getattr(request.user, 'username', 'System'),
                notes=f'Package receipt reprinted successfully (attempt {reprint_count + 1}/{settings.max_reprint_attempts}){edit_note}'
            )
            return Response({
                'message': 'Package receipt reprinted successfully',
                'attempts_used': reprint_count + 1,
                'max_attempts': settings.max_reprint_attempts,
                'recent_edit': recent_edit.notes if recent_edit else None
            })
        else:
            # Log history even if print failed
            PackageHistory.objects.create(
                package=package,
                action='reprint_failed',
                performed_by=getattr(request.user, 'username', 'System'),
                notes=f'Package receipt reprint failed - printer connection issue{edit_note}'
            )
            return Response(
                {'error': 'Failed to reprint package receipt - check printer connection'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        package = self.get_object()
        history = package.history.all()
        settings = AppSettings.get_settings()

        # Count reprint attempts
        reprint_count = PackageHistory.objects.filter(
            package=package,
            action='reprinted'
        ).count()

        data = [
            {
                'action': h.action,
                'old_status': h.old_status,
                'new_status': h.new_status,
                'performed_by': h.performed_by,
                'notes': h.notes,
                'timestamp': h.timestamp
            }
            for h in history
        ]

        return Response({
            'history': data,
            'reprint_info': {
                'attempts_used': reprint_count,
                'max_attempts': settings.max_reprint_attempts,
                'remaining_attempts': max(0, settings.max_reprint_attempts - reprint_count)
            }
        })

    def _print_receipt(self, package_data):
        try:
            settings = AppSettings.get_settings()
            printer = PackagePrinter(ip=settings.printer_ip, port=settings.printer_port, enable_qr=settings.enable_qr_codes)
            if not printer.print_label_receipt(package_data):
                logger.error(f"Failed to print label receipt for package {package_data['code']} - printer connection or configuration issue")
            else:
                logger.info(f"Successfully printed receipt for package {package_data['code']}")
        except Exception as e:
            logger.error(f"Exception during printing for package {package_data['code']}: {e}")


class AppSettingsViewSet(viewsets.ModelViewSet):
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer

    def get_queryset(self):
        # Ensure only one settings instance
        return AppSettings.objects.filter(pk=1)

    def get_object(self):
        # Always return the singleton settings
        return AppSettings.get_settings()

    def list(self, request):
        settings = AppSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def create(self, request):
        if AppSettings.objects.exists():
            return Response(
                {'error': 'Settings already exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request)

    def get_permissions(self):
        # Only admins can modify settings
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAdmin | IsStaff]
        return [permission() for permission in permission_classes]
        
