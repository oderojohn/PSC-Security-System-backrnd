import uuid
import threading
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
from lostfound.email.lost_match import send_report_acknowledgment, send_match_notification



User = get_user_model()
class ReportMixin:
    @action(detail=False, methods=['get'])
    def weekly_report(self, request):
        weeks_back = int(request.query_params.get('weeks', 4))
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks_back)

        lost_items = LostItem.objects.filter(date_reported__range=(start_date, end_date))
        lost_by_type = lost_items.values('type').annotate(count=Count('id'))

        found_items = FoundItem.objects.filter(date_reported__range=(start_date, end_date))
        found_by_type = found_items.values('type').annotate(count=Count('id'))

        claimed_count = found_items.filter(status='claimed').count()

        lost_daily_counts = (
            lost_items.annotate(day=TruncDay('date_reported')).values('day')
            .annotate(count=Count('id')).order_by('day')
        )

        found_daily_counts = (
            found_items.annotate(day=TruncDay('date_reported')).values('day')
            .annotate(count=Count('id')).order_by('day')
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


def safe_lower(value):
    """Lowercase safely, handle None as empty string."""
    return value.lower().strip() if isinstance(value, str) else ""


def calculate_match_score(lost_item, found_item):
    """Calculate similarity score between lost and found items."""

    # If types do not match, stop immediately (no score)
    if lost_item.type != found_item.type:
        return 0.0  

    scores = []

    # Type match bonus (only reached if same type)
    scores.append(0.3)

    # Name similarity
    name_similarity = SequenceMatcher(
        None, safe_lower(lost_item.item_name), safe_lower(found_item.item_name)
    ).ratio()
    scores.append(name_similarity * 0.2)

    # Description similarity
    desc_similarity = SequenceMatcher(
        None, safe_lower(lost_item.description), safe_lower(found_item.description)
    ).ratio()
    scores.append(desc_similarity * 0.2)

    # Location similarity
    location_similarity = SequenceMatcher(
        None, safe_lower(lost_item.place_lost), safe_lower(found_item.place_found)
    ).ratio()
    scores.append(location_similarity * 0.15)

    # Time difference score
    time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
    time_score = max(0, 1 - (time_diff / (7 * 24 * 3600)))  # Decay after 7 days
    scores.append(time_score * 0.15)

    return min(1.0, sum(scores))

def get_match_reasons(lost_item, found_item):
    """Return human-readable reasons for a match."""
    reasons = []

    if lost_item.type != found_item.type:
        return ["Different item types (no valid match)"]

    if lost_item.type == found_item.type:
        reasons.append(f"Matching type: {lost_item.type}")

    name_ratio = SequenceMatcher(None, safe_lower(lost_item.item_name), safe_lower(found_item.item_name)).ratio()
    if name_ratio > 0.7:
        reasons.append(f"Similar item names ({name_ratio:.0%} match)")

    desc_ratio = SequenceMatcher(None, safe_lower(lost_item.description), safe_lower(found_item.description)).ratio()
    if desc_ratio > 0.6:
        reasons.append(f"Similar descriptions ({desc_ratio:.0%} match)")

    loc_ratio = SequenceMatcher(None, safe_lower(lost_item.place_lost), safe_lower(found_item.place_found)).ratio()
    if loc_ratio > 0.7:
        reasons.append(f"Similar locations ({loc_ratio:.0%} match)")

    time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
    if time_diff < 24 * 3600:
        hours = int(time_diff / 3600)
        reasons.append(f"Reported within {hours} hour{'s' if hours != 1 else ''} of each other")

    return reasons


# --- Lost Item ViewSet ---
class LostItemViewSet(viewsets.ModelViewSet):
    queryset = LostItem.objects.all().order_by('-date_reported')
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]

    def perform_create(self, serializer):
        lost_item = serializer.save(
            reported_by=self.request.user,
            tracking_id=f"LI-{uuid.uuid4().hex[:8].upper()}"
        )

        days_back = 7
        similarity_threshold = 0.6
        recent_found_items = FoundItem.objects.filter(status='found')

        matches = []
        recipients = []
        for found_item in recent_found_items:
            score = calculate_match_score(lost_item, found_item)
            if score >= similarity_threshold:
                match_data = {
                    'lost_item': LostItemSerializer(lost_item).data,
                    'found_item': FoundItemSerializer(found_item).data,
                    'match_score': round(score * 100, 2),
                    'match_reasons': get_match_reasons(lost_item, found_item)
                }
                matches.append(match_data)
                recipients.append(lost_item.reporter_email)

                threading.Thread(
                    target=send_match_notification,
                    args=(lost_item, [match_data]),
                    daemon=True
                ).start()

        matches.sort(key=lambda x: x['match_score'], reverse=True)
        self.matches = matches
        self.recipients = recipients

        threading.Thread(
            target=send_report_acknowledgment,
            args=(lost_item,),
            daemon=True
        ).start()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if hasattr(self, 'matches') and self.matches:
            response.data['matches'] = self.matches
            response.data['acknowledgment'] = f"{len(self.matches)} matches found and emails sent to: {', '.join(set(self.recipients))}"
        else:
            response.data['acknowledgment'] = "Acknowledgment email sent to reporter."
        return response

    def get_queryset(self):
        qs = super().get_queryset()
        item_type = self.request.query_params.get('type')  # ?type=card OR ?type=item

        if item_type == 'card':
            qs = qs.filter(type='card')
        elif item_type == 'item':
            qs = qs.filter(type='item')

        return qs


# --- Found Item ViewSet ---
class FoundItemViewSet(viewsets.ModelViewSet):
    queryset = FoundItem.objects.all().order_by('-date_reported')
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]

    def perform_create(self, serializer):
        found_item = serializer.save(reported_by=self.request.user,
        status="found" # Ensure status is set to 'found' on creation
        )
        PackagePrinter().print_found_receipt(found_item)

        similarity_threshold = 0.5
        recent_lost_items = LostItem.objects.all()

        matches_sent = []
        recipients = []
        for lost_item in recent_lost_items:
            score = calculate_match_score(lost_item, found_item)
            if score >= similarity_threshold:
                match_data = {
                    'lost_item': LostItemSerializer(lost_item).data,
                    'found_item': FoundItemSerializer(found_item).data,
                    'match_score': round(score * 100, 2),
                    'match_reasons': get_match_reasons(lost_item, found_item),
                    'sent_to': lost_item.reporter_email
                }
                send_match_notification(lost_item, [match_data])
                matches_sent.append(match_data)
                recipients.append(lost_item.reporter_email)

        self.matches_sent = matches_sent
        self.recipients = recipients

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if hasattr(self, 'matches_sent') and self.matches_sent:
            response.data['matches'] = self.matches_sent

            # ✅ Clean recipients: remove None/empty and force str
            valid_recipients = [str(r) for r in getattr(self, 'recipients', []) if r]

            if valid_recipients:
                response.data['acknowledgment'] = (
                    f"{len(self.matches_sent)} matches found and emails sent to: {', '.join(set(valid_recipients))}"
                )
            else:
                response.data['acknowledgment'] = f"{len(self.matches_sent)} matches found, but no valid email recipients."
        else:
            response.data['acknowledgment'] = "Acknowledgment email sent to reporter."

        return response

    
    @action(detail=False, methods=['get'], url_path='generate_matches')
    def generate_matches(self, request):
        similarity_threshold = 0.5
        tracking_id = request.query_params.get('tracking_id')

        lost_items = LostItem.objects.all()
        found_items = FoundItem.objects.all()

        if tracking_id:
            lost_items = lost_items.filter(tracking_id=tracking_id) | lost_items.none()
            found_items = found_items.filter(tracking_id=tracking_id) | found_items.none()

        matches = []
        for lost in lost_items:
            for found in found_items:
                if lost.type != found.type:  # ✅ enforce type matching
                    continue
                score = calculate_match_score(lost, found)
                if score >= similarity_threshold:
                    matches.append({
                        'lost_item': LostItemSerializer(lost).data,
                        'found_item': FoundItemSerializer(found).data,
                        'match_score': round(score * 100, 2),
                        'match_reasons': get_match_reasons(lost, found)
                    })

        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return Response({'matches': matches})
    @action(detail=False, methods=['post'], url_path='print_match')
    def print_match(self, request):
        """
        Print a chit for matches by tracking_id.
        - If tracking_id belongs to a LostItem.tracking_id -> match that lost item against all found items.
        - If tracking_id is a FoundItem.id (integer) -> match that found item against all lost items.
        """
        tracking_id = request.query_params.get('tracking_id')
        if not tracking_id:
            return Response(
                {"error": "tracking_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        lost_items = None
        found_items = None

        # Case 1: Looks like a LostItem tracking_id
        if tracking_id.startswith("LI-"):
            lost_items = LostItem.objects.filter(tracking_id=tracking_id)
            if not lost_items.exists():
                return Response(
                    {"error": f"No LostItem found for tracking_id={tracking_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            found_items = FoundItem.objects.all()

        else:
            # Case 2: Must be a FoundItem.id (integer)
            try:
                found_item_id = int(tracking_id)
                found_item = FoundItem.objects.get(id=found_item_id)
                found_items = [found_item]
                lost_items = LostItem.objects.all()
            except (ValueError, FoundItem.DoesNotExist):
                return Response(
                    {"error": f"No LostItem or FoundItem found for tracking_id={tracking_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )

        similarity_threshold = 0.5
        matches = []

        for lost in lost_items:
            for found in found_items:
                if lost.type != found.type:
                    continue
                score = calculate_match_score(lost, found)
                if score >= similarity_threshold:
                    match_data = {
                        "lost_item": LostItemSerializer(lost).data,
                        "found_item": FoundItemSerializer(found).data,
                        "match_score": round(score * 100, 2),
                        "match_reasons": get_match_reasons(lost, found),
                    }
                    matches.append(match_data)
                    PackagePrinter().print_match_receipt(match_data)

        if not matches:
            return Response(
                {"message": f"No matches found for tracking_id={tracking_id}"},
                status=status.HTTP_200_OK
            )

        return Response({
            "status": "success",
            "acknowledgment": f"{len(matches)} match chit(s) printed for tracking_id={tracking_id}",
            "matches": matches
        }, status=status.HTTP_200_OK)
    def get_queryset(self):
        qs = super().get_queryset()
        item_type = self.request.query_params.get('type')  # ?type=card or ?type=item

        if item_type == 'card':
            qs = qs.filter(type='card')
        elif item_type == 'item':
            qs = qs.exclude(type='card')

        return qs


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

    @action(detail=False, methods=['get'], url_path='pickuphistory', url_name='pickup-history')
    def pickuphistory(self, request):
        """
        Return the last N picked items with their associated found item details.
        Supports optional ?limit=N (default 20)
        """
        try:
            limit = int(request.query_params.get('limit', 20))
            limit = max(1, min(limit, 100))
        except (ValueError, TypeError):
            limit = 20

        recent_pickups = PickupLog.objects.select_related('item').order_by('-pickup_date')[:limit]

        data = []
        for pickup in recent_pickups:
            pickup_data = PickupLogSerializer(pickup).data
            item_data = FoundItemSerializer(pickup.item).data
            data.append({
                'pickup_details': pickup_data,
                'item_details': item_data,
                'pickup_date': pickup.pickup_date,
                'verified_by': pickup.verified_by.get_full_name() if pickup.verified_by else str(pickup.verified_by)
            })

        return Response(data, status=status.HTTP_200_OK)