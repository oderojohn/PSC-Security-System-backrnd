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
    card_last_four = models.CharField(max_length=6, blank=True, null=True)
    place_lost = models.CharField(max_length=200, blank=True, null=True)
    reporter_phone = models.CharField(max_length=20, blank=True, null=True)
    reporter_email = models.EmailField(blank=True, null=True)
    reporter_member_id = models.CharField(max_length=20, blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lost_items')
    tracking_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    photo = models.ImageField(upload_to="lost_items/photos/", blank=True, null=True)

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
    card_last_four = models.CharField(max_length=6, blank=True, null=True)
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


class EmailLog(models.Model):
    """Model to track sent emails for rate limiting"""
    EMAIL_TYPES = [
        ('acknowledgment', 'Acknowledgment'),
        ('match_notification', 'Match Notification'),
    ]

    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    recipient = models.EmailField()
    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)
    subject = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.email_type} to {self.recipient} at {self.sent_at}"

    @classmethod
    def can_send_email(cls, email_type, recipient, lost_item=None):
        """Check if we can send an email based on limits"""
        from django.utils import timezone
        from datetime import timedelta

        max_per_day = int(SystemSettings.get_setting('max_auto_emails_per_day', 50))
        max_per_item = int(SystemSettings.get_setting('max_auto_emails_per_item', 3))

        # Check daily limit
        today = timezone.now().date()
        daily_count = cls.objects.filter(sent_at__date=today).count()
        if daily_count >= max_per_day:
            return False, "Daily email limit reached"

        # Check per item limit
        if lost_item:
            item_count = cls.objects.filter(lost_item=lost_item).count()
            if item_count >= max_per_item:
                return False, "Per-item email limit reached"

        return True, "OK"


class SystemSettings(models.Model):
    """Model for configurable system settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key"""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description=""):
        """Set or update a setting"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            setting.description = description
            setting.save()
        return setting
