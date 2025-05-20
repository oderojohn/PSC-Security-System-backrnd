from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from .models import LostItem, FoundItem, PickupLog
from .serializers import (
    LostItemSerializer, 
    FoundItemSerializer, 
    PickupLogSerializer,
    ItemStatsSerializer,
    WeeklyReportSerializer
)
from .permissions import IsStaffOrReadOnly
from difflib import SequenceMatcher
from datetime import timedelta, datetime
from django.utils import timezone
from django.http import HttpResponse
import csv
from reportlab.pdfgen import canvas
from io import BytesIO
from .PackagePrinter import PackagePrinter
from collections import defaultdict
from django.db.models.functions import TruncDay



User = get_user_model()
class ReportMixin:
    @action(detail=False, methods=['get'])
    def weekly_report(self, request):
        """Generate a weekly report of items"""
        weeks_back = int(request.query_params.get('weeks', 4))
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        # Lost items stats
        lost_items = LostItem.objects.filter(date_reported__range=(start_date, end_date))
        lost_by_type = lost_items.values('type').annotate(count=Count('id'))
        
        # Found items stats
        found_items = FoundItem.objects.filter(date_reported__range=(start_date, end_date))
        found_by_type = found_items.values('type').annotate(count=Count('id'))
        
        # Claimed items
        claimed_count = found_items.filter(status='claimed').count()
        
        # Daily counts for lost items
        lost_daily_counts = (
            lost_items
            .annotate(day=TruncDay('date_reported'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        # Daily counts for found items
        found_daily_counts = (
            found_items
            .annotate(day=TruncDay('date_reported'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'lost_items_total': lost_items.count(),
            'lost_items_by_type': list(lost_by_type),
            'found_items_total': found_items.count(),
            'found_items_by_type': list(found_by_type),
            'claimed_items_count': claimed_count,
            'claim_rate': claimed_count / found_items.count() if found_items.count() > 0 else 0,
            'lost_items_daily': list(lost_daily_counts),
            'found_items_daily': list(found_daily_counts),
        }
        
        serializer = WeeklyReportSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LostItemViewSet(ReportMixin, viewsets.ModelViewSet):
    queryset = LostItem.objects.all().order_by('-date_reported')
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        time_frame = self.request.query_params.get('time_frame', None)
        
        if status:
            queryset = queryset.filter(status=status)
            
        if search:
            queryset = queryset.filter(
                Q(item_name__icontains=search) |
                Q(description__icontains=search) |
                Q(card_last_four__icontains=search) |
                Q(owner_name__icontains=search) |
                Q(place_lost__icontains=search) |
                Q(reporter_member_id__icontains=search)
            )
            
        if time_frame:
            now = timezone.now()
            if time_frame == 'today':
                queryset = queryset.filter(date_reported__date=now.date())
            elif time_frame == 'week':
                queryset = queryset.filter(date_reported__gte=now - timedelta(days=7))
            elif time_frame == 'month':
                queryset = queryset.filter(date_reported__gte=now - timedelta(days=30))
                
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
        """Mark a lost item as found and create corresponding found item"""
        lost_item = self.get_object()
        found_item_data = {
            'type': lost_item.type,
            'owner_name': lost_item.owner_name,
            'reported_by': lost_item.reported_by.id,
            'item_name': lost_item.item_name,
            'description': lost_item.description,
            'card_last_four': lost_item.card_last_four,
            'place_found': lost_item.place_lost,
            'finder_phone': lost_item.reporter_phone,
            'finder_name': lost_item.reported_by.get_full_name() or str(lost_item.reported_by),
            'status': 'found'
        }
        
        found_item_serializer = FoundItemSerializer(data=found_item_data)
        if found_item_serializer.is_valid():
            found_item = found_item_serializer.save()
            lost_item.delete()
            
            # Print receipt for the found item
            printer = PackagePrinter()
            printer.print_found_receipt(found_item)
            
            return Response(found_item_serializer.data, status=status.HTTP_201_CREATED)
        return Response(found_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def potential_matches(self, request):
        """Find potential matches between lost and found items"""
        days_back = int(request.query_params.get('days', 7))
        similarity_threshold = float(request.query_params.get('similarity', 0.6))
        
        lost_items = LostItem.objects.filter(
            status='pending',
            date_reported__gte=timezone.now() - timedelta(days=days_back))
        
        found_items = FoundItem.objects.filter(
            status='found',
            date_reported__gte=timezone.now() - timedelta(days=days_back))
        
        matches = []
        for lost_item in lost_items:
            for found_item in found_items:
                score = self.calculate_match_score(lost_item, found_item)
                if score >= similarity_threshold:
                    matches.append({
                        'lost_item': LostItemSerializer(lost_item).data,
                        'found_item': FoundItemSerializer(found_item).data,
                        'match_score': score,
                        'match_reasons': self.get_match_reasons(lost_item, found_item, score)
                    })
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return Response(matches)
    
    def calculate_match_score(self, lost_item, found_item):
        """Calculate similarity score between lost and found items"""
        scores = []
        
        # Type match
        if lost_item.type == found_item.type:
            scores.append(0.3)
        
        # Name similarity
        name_similarity = SequenceMatcher(
            None, 
            lost_item.item_name.lower(), 
            found_item.item_name.lower()
        ).ratio()
        scores.append(name_similarity * 0.2)
        
        # Description similarity
        desc_similarity = SequenceMatcher(
            None, 
            lost_item.description.lower(), 
            found_item.description.lower()
        ).ratio()
        scores.append(desc_similarity * 0.2)
        
        # Location similarity
        location_similarity = SequenceMatcher(
            None, 
            lost_item.place_lost.lower(), 
            found_item.place_found.lower()
        ).ratio()
        scores.append(location_similarity * 0.15)
        
        # Time proximity
        time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
        time_score = max(0, 1 - (time_diff / (7 * 24 * 3600)))  # Normalize to 1 week
        scores.append(time_score * 0.15)
        
        return min(1.0, sum(scores))
    
    def get_match_reasons(self, lost_item, found_item, score):
        """Generate human-readable match reasons"""
        reasons = []
        if lost_item.type == found_item.type:
            reasons.append(f"Matching type: {lost_item.type}")
        
        name_ratio = SequenceMatcher(
            None, lost_item.item_name.lower(), found_item.item_name.lower()).ratio()
        if name_ratio > 0.7:
            reasons.append(f"Similar item names ({name_ratio:.0%} match)")
        
        desc_ratio = SequenceMatcher(
            None, lost_item.description.lower(), found_item.description.lower()).ratio()
        if desc_ratio > 0.6:
            reasons.append(f"Similar descriptions ({desc_ratio:.0%} match)")
        
        loc_ratio = SequenceMatcher(
            None, lost_item.place_lost.lower(), found_item.place_found.lower()).ratio()
        if loc_ratio > 0.7:
            reasons.append(f"Similar locations ({loc_ratio:.0%} match)")
        
        time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
        if time_diff < 24 * 3600:
            hours = int(time_diff / 3600)
            reasons.append(f"Reported within {hours} hour{'s' if hours != 1 else ''} of each other")
        
        return reasons


class FoundItemViewSet(ReportMixin, viewsets.ModelViewSet):
    queryset = FoundItem.objects.all().order_by('-date_reported')
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def perform_create(self, serializer):
        found_item = serializer.save(reported_by=self.request.user)
        
        # Print receipt
        printer = PackagePrinter()
        print_success = printer.print_found_receipt(found_item)
        
        if not print_success:
            # Log printing failure (you might want to add proper logging here)
            pass
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        time_frame = self.request.query_params.get('time_frame', None)
        
        if status:
            queryset = queryset.filter(status=status)
            
        if search:
            queryset = queryset.filter(
                Q(item_name__icontains=search) |
                Q(description__icontains=search) |
                Q(card_last_four__icontains=search) |
                Q(owner_name__icontains=search) |
                Q(place_found__icontains=search) |
                Q(finder_name__icontains=search)
            )
            
        if time_frame:
            now = timezone.now()
            if time_frame == 'today':
                queryset = queryset.filter(date_reported__date=now.date())
            elif time_frame == 'week':
                queryset = queryset.filter(date_reported__gte=now - timedelta(days=7))
            elif time_frame == 'month':
                queryset = queryset.filter(date_reported__gte=now - timedelta(days=30))
                
        return queryset
    
    @action(detail=True, methods=['post'])
    def pick(self, request, pk=None):
        """Handle item pickup and create pickup log"""
        found_item = self.get_object()
        
        if found_item.status == 'claimed':
            return Response(
                {'error': 'Item has already been claimed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pickup_data = {
            'item': found_item.id,
            'picked_by_member_id': request.data.get('memberId'),
            'picked_by_name': request.data.get('name'),
            'picked_by_phone': request.data.get('phone'),
            'verified_by': request.user.id
        }
        
        pickup_serializer = PickupLogSerializer(data=pickup_data)
        if pickup_serializer.is_valid():
            pickup_log = pickup_serializer.save()
            found_item.status = 'claimed'
            found_item.save()
            
            # Print pickup receipt
            printer = PackagePrinter()
            printer.print_pickup_receipt(pickup_log)
            
            return Response(pickup_serializer.data, status=status.HTTP_201_CREATED)
        return Response(pickup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemStatsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get summary statistics for lost and found items"""
        # Current stats
        stats = {
            'lost': {
                'total': LostItem.objects.count(),
                'pending': LostItem.objects.filter(status='pending').count(),
                'recent': LostItem.objects.filter(
                    date_reported__gte=timezone.now() - timedelta(days=7)).count(),
            },
            'found': {
                'total': FoundItem.objects.count(),
                'unclaimed': FoundItem.objects.filter(status='found').count(),
                'claimed': FoundItem.objects.filter(status='claimed').count(),
                'recent': FoundItem.objects.filter(
                    date_reported__gte=timezone.now() - timedelta(days=7)).count(),
            },
            'pickups': {
                'total': PickupLog.objects.count(),
                'recent': PickupLog.objects.filter(
                    pickup_date__gte=timezone.now() - timedelta(days=7)).count(),
            }
        }
        
        # Weekly trends
        weekly_trends = defaultdict(lambda: {
            'lost': 0,
            'found': 0,
            'claimed': 0
        })
        
        # Last 8 weeks data
        for i in range(8):
            week_start = timezone.now() - timedelta(weeks=(8-i))
            week_end = week_start + timedelta(weeks=1)
            
            key = week_start.strftime('%Y-%m-%d')
            weekly_trends[key]['lost'] = LostItem.objects.filter(
                date_reported__range=(week_start, week_end)).count()
            weekly_trends[key]['found'] = FoundItem.objects.filter(
                date_reported__range=(week_start, week_end)).count()
            weekly_trends[key]['claimed'] = FoundItem.objects.filter(
                status='claimed',
                date_reported__range=(week_start, week_end)).count()
        
        stats['weekly_trends'] = weekly_trends
        
        serializer = ItemStatsSerializer(data=stats)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PickupLogViewSet(ReportMixin, viewsets.ModelViewSet):
    queryset = PickupLog.objects.all().order_by('-pickup_date')
    serializer_class = PickupLogSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        time_frame = self.request.query_params.get('time_frame', None)
        
        if search:
            queryset = queryset.filter(
                Q(picked_by_name__icontains=search) |
                Q(picked_by_member_id__icontains=search) |
                Q(item__item_name__icontains=search) |
                Q(item__owner_name__icontains=search)
            )
            
        if time_frame:
            now = timezone.now()
            if time_frame == 'today':
                queryset = queryset.filter(pickup_date__date=now.date())
            elif time_frame == 'week':
                queryset = queryset.filter(pickup_date__gte=now - timedelta(days=7))
            elif time_frame == 'month':
                queryset = queryset.filter(pickup_date__gte=now - timedelta(days=30))
                
        return queryset