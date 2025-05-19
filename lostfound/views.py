from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import LostItem, FoundItem, PickupLog
from .serializers import (
    LostItemSerializer, 
    FoundItemSerializer, 
    PickupLogSerializer,
    ItemStatsSerializer
)
from .permissions import IsStaffOrReadOnly
from difflib import SequenceMatcher
from datetime import timedelta
from django.utils import timezone
from .PackagePrinter import PackagePrinter
User = get_user_model()

class LostItemViewSet(viewsets.ModelViewSet):
    queryset = LostItem.objects.all()
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
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
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
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
            return Response(found_item_serializer.data, status=status.HTTP_201_CREATED)
        return Response(found_item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def potential_matches(self, request):
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
        scores = []
        if lost_item.type == found_item.type:
            scores.append(0.3)
        
        name_similarity = SequenceMatcher(None, lost_item.item_name.lower(), found_item.item_name.lower()).ratio()
        scores.append(name_similarity * 0.2)
        
        desc_similarity = SequenceMatcher(None, lost_item.description.lower(), found_item.description.lower()).ratio()
        scores.append(desc_similarity * 0.2)
        
        location_similarity = SequenceMatcher(None, lost_item.place_lost.lower(), found_item.place_found.lower()).ratio()
        scores.append(location_similarity * 0.15)
        
        time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
        time_score = max(0, 1 - (time_diff / (7 * 24 * 3600)))
        scores.append(time_score * 0.15)
        
        return min(1.0, sum(scores))
    
    def get_match_reasons(self, lost_item, found_item, score):
        reasons = []
        if lost_item.type == found_item.type:
            reasons.append(f"Matching type: {lost_item.type}")
        if SequenceMatcher(None, lost_item.item_name.lower(), found_item.item_name.lower()).ratio() > 0.7:
            reasons.append(f"Similar item names: '{lost_item.item_name}' and '{found_item.item_name}'")
        if SequenceMatcher(None, lost_item.description.lower(), found_item.description.lower()).ratio() > 0.6:
            reasons.append("Similar descriptions")
        if SequenceMatcher(None, lost_item.place_lost.lower(), found_item.place_found.lower()).ratio() > 0.7:
            reasons.append(f"Similar locations: '{lost_item.place_lost}' and '{found_item.place_found}'")
        
        time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
        if time_diff < 24 * 3600:
            reasons.append(f"Reported within {int(time_diff/3600)} hours of each other")
        return reasons


class ItemStatsView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        stats = {
            'lost_count': LostItem.objects.count(),
            'found_count': FoundItem.objects.count(),
            'pending_count': LostItem.objects.filter(status='pending').count()
        }
        serializer = ItemStatsSerializer(data=stats)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MatchSerializer(serializers.Serializer):
    lost_item = LostItemSerializer()
    found_item = FoundItemSerializer()
    match_score = serializers.FloatField()
    match_reasons = serializers.ListField(child=serializers.CharField())
    
class FoundItemViewSet(viewsets.ModelViewSet):
    queryset = FoundItem.objects.all()
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def perform_create(self, serializer):
        # Save the found item first
        found_item = serializer.save(reported_by=self.request.user)
        
        # Print the receipt after saving
        printer = PackagePrinter()
        print_success = printer.print_found_receipt(found_item)
        
        if not print_success:
            # You might want to log this or handle it differently
            print("Failed to print receipt, but item was saved")
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', None)
        
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
        return queryset
    
    @action(detail=True, methods=['post'])
    def pick(self, request, pk=None):
        found_item = self.get_object()
        pickup_data = {
            'item': found_item.id,
            'picked_by_member_id': request.data.get('memberId'),
            'picked_by_name': request.data.get('name'),
            'picked_by_phone': request.data.get('phone'),
            'verified_by': request.user.id
        }
        
        pickup_serializer = PickupLogSerializer(data=pickup_data)
        if pickup_serializer.is_valid():
            pickup_serializer.save()
            found_item.status = 'claimed'
            found_item.save()
            return Response(pickup_serializer.data, status=status.HTTP_201_CREATED)
        return Response(pickup_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MatchSerializer(serializers.Serializer):
    lost_item = LostItemSerializer()
    found_item = FoundItemSerializer()
    match_score = serializers.FloatField()
    match_reasons = serializers.ListField(child=serializers.CharField())