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
from users.models import EventLog  # Import EventLog from users app
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'code',
        'description',
        'recipient_name',
        'recipient_phone',
        'dropped_by',
        'picked_by',
        'shelf'  
    ]
    filterset_fields = ['status', 'type', 'shelf']

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    def _log_event(self, action, package, request, metadata=None):
        """Helper method to log package-related events"""
        try:
            EventLog.objects.create(
                user=request.user,
                action=action,
                object_type='Package',
                object_id=package.id,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata or {
                    'code': package.code,
                    'status': package.get_status_display(),
                    'shelf': package.shelf,
                    'type': package.get_type_display()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log event: {str(e)}")

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        
        if status_param == 'pending':
            queryset = queryset.filter(status=Package.PENDING)
        elif status_param == 'picked':
            queryset = queryset.filter(status=Package.PICKED)
            
        return queryset

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
            serializer.save()
            
            # Log package pick event
            self._log_event(
                action=EventLog.ActionTypes.UPDATE,
                package=package,
                request=request,
                metadata={
                    'old_status': old_status,
                    'new_status': Package.PICKED,
                    'picked_by': request.data.get('picked_by'),
                    'picked_time': now().isoformat(),
                    'shelf_cleared': True
                }
            )
            
            response_data = serializer.data
            response_data['shelf'] = None
            return Response(
                response_data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        pending_count = Package.objects.filter(status=Package.PENDING).count()
        picked_count = Package.objects.filter(status=Package.PICKED).count()
        total_count = Package.objects.count()
        
        # Log stats access
        try:
            EventLog.objects.create(
                user=request.user,
                action=EventLog.ActionTypes.ACCESS,
                object_type='PackageStats',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'pending_count': pending_count,
                    'picked_count': picked_count,
                    'total_count': total_count
                }
            )
        except Exception as e:
            logger.error(f"Failed to log stats access: {str(e)}")

        return Response({
            'pending': pending_count,
            'picked': picked_count,
            'total': total_count,
            'shelves_occupied': Package.objects.filter(status=Package.PENDING).values('shelf').distinct().count()
        })

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin | IsReception]
        elif self.action in ['pick']:
            permission_classes = [IsStaff | IsReception]
        else:
            permission_classes = [IsStaff]
        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            serializer = PackageSerializer(data=request.data)
            if serializer.is_valid():
                package = serializer.save()
                
                # Log package creation
                self._log_event(
                    action=EventLog.ActionTypes.CREATE,
                    package=package,
                    request=request,
                    metadata={
                        **serializer.data,
                        'printed': False  
                    }
                )
                
                # Prepare data for printing
                print_data = {
                    'code': package.code,
                    'type': package.get_type_display(),
                    'description': package.description,
                    'recipient_name': package.recipient_name,
                    'recipient_phone': package.recipient_phone,
                    'dropped_by': package.dropped_by,
                    'dropper_phone': package.dropper_phone,
                    'shelf': package.shelf,
                    'created_by': request.user.username , 
                }
                
                # Print receipt in background thread
                print_thread = Thread(
                    target=self._print_receipt,
                    args=(print_data, request, package),
                    daemon=True
                )
                print_thread.start()
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error creating package")
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store old data before update
        old_data = PackageSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Log package update
        self._log_event(
            action=EventLog.ActionTypes.UPDATE,
            package=instance,
            request=request,
            metadata={
                'old_data': old_data,
                'new_data': serializer.data,
                'updated_fields': request.data.keys()
            }
        )
        
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Log package deletion before actual deletion
        self._log_event(
            action=EventLog.ActionTypes.DELETE,
            package=instance,
            request=request,
            metadata=PackageSerializer(instance).data
        )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _print_receipt(self, package_data, request, package):
        printer = PackagePrinter()
        print_success = printer.print_package_receipt(package_data)
        
        # Update the creation log with print status
        try:
            creation_log = EventLog.objects.filter(
                object_id=package.id,
                action=EventLog.ActionTypes.CREATE
            ).latest('timestamp')
            
            creation_log.metadata['printed'] = print_success
            creation_log.metadata['print_time'] = now().isoformat()
            creation_log.save()
            
            if print_success:
                # Additional log for successful printing
                self._log_event(
                    action=EventLog.ActionTypes.SYSTEM,
                    package=package,
                    request=request,
                    metadata={
                        'event': 'receipt_printed',
                        'printer_status': 'success'
                    }
                )
        except EventLog.DoesNotExist:
            logger.warning(f"No creation log found for package {package.id}")

        if not print_success:
            logger.error(f"Failed to print receipt for package {package_data['code']}")
            # Log printing failure
            self._log_event(
                action=EventLog.ActionTypes.SYSTEM,
                package=package,
                request=request,
                metadata={
                    'event': 'print_failed',
                    'error': 'Receipt printing failed'
                }
            )