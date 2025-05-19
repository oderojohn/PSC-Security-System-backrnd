from celery import shared_task
from django.utils import timezone
from .models import LostItem, FoundItem
from difflib import SequenceMatcher

@shared_task
def check_for_potential_matches():
    lost_items = LostItem.objects.filter(
        status='pending',
        date_reported__gte=timezone.now() - timezone.timedelta(days=7))
    
    found_items = FoundItem.objects.filter(
        status='found',
        date_reported__gte=timezone.now() - timezone.timedelta(days=7))
    
    matches_found = 0
    
    for lost_item in lost_items:
        for found_item in found_items:
            score = calculate_match_score(lost_item, found_item)
            if score >= 0.7:
                matches_found += 1
    
    return f"Found {matches_found} potential matches (No emails sent)"

def calculate_match_score(lost_item, found_item):
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