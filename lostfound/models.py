from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
User = get_user_model()

class BaseItem(models.Model):
    CARD = 'card'
    ITEM = 'item'
    TYPE_CHOICES = [
        (CARD, 'Card'),
        (ITEM, 'Item'),
    ]
    
    PENDING = 'pending'
    FOUND = 'found'
    CLAIMED = 'claimed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (FOUND, 'Found'),
        (CLAIMED, 'Claimed'),
    ]
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    date_reported = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class LostItem(BaseItem):
    item_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    card_last_four = models.CharField(max_length=5, blank=True, null=True)
    place_lost = models.CharField(max_length=200, blank=True, null=True)
    reporter_phone = models.CharField(max_length=20, blank=True, null=True)
    reporter_email = models.EmailField(blank=True, null=True)
    reporter_member_id = models.CharField(max_length=20, blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lost_items')
    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = f"LI-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


    def __str__(self):
        if self.type == self.CARD:
            return f"Lost Card ({self.card_last_four})"
        return f"Lost {self.item_name}"

class FoundItem(BaseItem):
    item_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    card_last_four = models.CharField(max_length=5, blank=True, null=True)
    place_found = models.CharField(max_length=200, blank=True, null=True)
    finder_phone = models.CharField(max_length=20, blank=True, null=True)
    finder_name = models.CharField(max_length=100, blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='found_items')
    photo = models.ImageField(upload_to="found_items/photos/", blank=True, null=True) 

    def __str__(self):
        if self.type == self.CARD:
            return f"Found Card ({self.card_last_four})"
        return f"Found {self.item_name}"



class PickupLog(models.Model):
    item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='pickup_logs')
    picked_by_member_id = models.CharField(max_length=20)
    picked_by_name = models.CharField(max_length=100)
    picked_by_phone = models.CharField(max_length=20)
    pickup_date = models.DateTimeField(default=timezone.now)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Pickup by {self.picked_by_name} on {self.pickup_date}"
