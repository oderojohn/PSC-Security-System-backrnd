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
    filterset_fields = ['status', 'type', 'shelf']  # filter  by s.t.s
    
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
            serializer.save()
            # Include shelf in response (will be None after picking)
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
        
        return Response({
            'pending': pending_count,
            'picked': picked_count,
            'total': total_count,
            'shelves_occupied': Package.objects.filter(status=Package.PENDING).values('shelf').distinct().count()
        })
        
    def create(self, request):
        try:
            serializer = PackageSerializer(data=request.data)
            if serializer.is_valid():
                package = serializer.save()
                
                # Prepare data for printing
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
                
                # Print receipt in background thread
                print_thread = Thread(
                    target=self._print_receipt,
                    args=(print_data,),
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
    
    def _print_receipt(self, package_data):
        printer = PackagePrinter()
        if not printer.print_package_receipt(package_data):
            logger.error(f"Failed to print receipt for package {package_data['code']}")