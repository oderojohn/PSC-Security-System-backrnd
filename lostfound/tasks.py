from celery import shared_task
from django.utils import timezone
from .models import LostItem, FoundItem, SystemSettings
from difflib import SequenceMatcher

@shared_task
def check_for_potential_matches():
    days_back = int(SystemSettings.get_setting('task_match_days_back', 7))
    threshold = float(SystemSettings.get_setting('task_match_threshold', 0.7))

    lost_items = LostItem.objects.filter(
        status='pending',
        date_reported__gte=timezone.now() - timezone.timedelta(days=days_back))

    found_items = FoundItem.objects.filter(
        status='found',
        date_reported__gte=timezone.now() - timezone.timedelta(days=days_back))

    matches_found = 0

    for lost_item in lost_items:
        for found_item in found_items:
            score = calculate_match_score(lost_item, found_item)
            if score >= threshold:
                matches_found += 1

    return f"Found {matches_found} potential matches (No emails sent)"

def calculate_match_score(lost_item, found_item):
    """Calculate similarity score between lost and found items."""

    # If types do not match, stop immediately (no score)
    if lost_item.type != found_item.type:
        return 0.0

    # Special handling for card type items - only compare card numbers
    if lost_item.type == 'card':
        lost_card = (lost_item.card_last_four or "").lower().strip()
        found_card = (found_item.card_last_four or "").lower().strip()

        if lost_card and found_card and lost_card == found_card:
            return 1.0  # Exact card match
        else:
            return 0.0  # No match

    # Regular item matching logic
    scores = []
    total_weight = 0

    # Type match bonus (only reached if same type)
    scores.append(0.3)
    total_weight += 0.3

    # Name similarity
    lost_name = (lost_item.item_name or "").lower().strip()
    found_name = (found_item.item_name or "").lower().strip()

    if lost_name and found_name:
        name_similarity = SequenceMatcher(None, lost_name, found_name).ratio()
        scores.append(name_similarity * 0.25)
        total_weight += 0.25
    elif lost_name or found_name:
        scores.append(0.1)
        total_weight += 0.1

    # Description similarity
    lost_desc = (lost_item.description or "").lower().strip()
    found_desc = (found_item.description or "").lower().strip()

    if lost_desc and found_desc:
        desc_similarity = SequenceMatcher(None, lost_desc, found_desc).ratio()
        scores.append(desc_similarity * 0.2)
        total_weight += 0.2
    elif lost_desc or found_desc:
        scores.append(0.05)
        total_weight += 0.05

    # Location similarity
    lost_location = (lost_item.place_lost or "").lower().strip()
    found_location = (found_item.place_found or "").lower().strip()

    if lost_location and found_location:
        location_similarity = SequenceMatcher(None, lost_location, found_location).ratio()
        scores.append(location_similarity * 0.15)
        total_weight += 0.15
    elif lost_location or found_location:
        scores.append(0.05)
        total_weight += 0.05

    # Time difference score
    time_diff = abs((lost_item.date_reported - found_item.date_reported).total_seconds())
    time_score = max(0, 1 - (time_diff / (14 * 24 * 3600)))  # Decay after 14 days
    scores.append(time_score * 0.1)
    total_weight += 0.1

    # Normalize score based on available data
    if total_weight > 0:
        final_score = sum(scores) / total_weight
        return min(1.0, final_score)
    else:
        return 0.0