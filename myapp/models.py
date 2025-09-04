# models.py
from django.db import models
from django.utils import timezone
import random
import string

MAX_SHELF_NUMBER = 200

# --- Random suffix for code generation ---
def generate_random_suffix(k=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))

# --- Get next available shelf for a given letter prefix ---
def get_letter_based_shelf(letter):
    prefix = letter.upper()
    existing_shelves = set(
        Package.objects.filter(status=Package.PENDING, shelf__startswith=prefix)
        .values_list('shelf', flat=True)
    )
    for i in range(1, MAX_SHELF_NUMBER + 1):
        shelf = f"{prefix}{i}"
        if shelf not in existing_shelves:
            return shelf
    return None  # All shelves used for that letter

# --- Generate package code prefixed with shelf ---
def generate_package_code(shelf):
    while True:
        suffix = generate_random_suffix(5)
        code = f"{shelf}{suffix}"
        if not Package.objects.filter(code=code).exists():
            return code

class Package(models.Model):
    PACKAGE = 'package'
    DOCUMENT = 'document'
    KEYS = 'keys'
    TYPE_CHOICES = [
        (PACKAGE, 'Package'),
        (DOCUMENT, 'Document'),
        (KEYS, 'keys'),
    ]

    PENDING = 'pending'
    PICKED = 'picked'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PICKED, 'Picked'),
    ]

    code = models.CharField(max_length=32, unique=True, editable=False)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PACKAGE)
    description = models.TextField()
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    recipient_id = models.CharField(max_length=6, blank=True, null=True, help_text='Recipient ID (max 6 characters, e.g., kwe45, k1234s)')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    dropped_by = models.CharField(max_length=100)
    dropper_phone = models.CharField(max_length=20, blank=True, null=True)
    dropper_id = models.CharField(max_length=6, blank=True, null=True, help_text='Member number (max 6 characters)')

    picked_by = models.CharField(max_length=100, blank=True, null=True)
    picker_phone = models.CharField(max_length=20, blank=True, null=True)
    picker_id = models.CharField(max_length=6, blank=True, null=True, help_text='Picker member number (max 6 characters)')
    picked_at = models.DateTimeField(blank=True, null=True)

    shelf = models.CharField(max_length=10, blank=True, null=True, editable=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if self.status == self.PENDING:
            if not self.shelf:
                first_letter = self.recipient_name.strip()[0].upper() if self.recipient_name else 'X'
                self.shelf = get_letter_based_shelf(first_letter)
            if not self.code:
                self.code = generate_package_code(self.shelf)
        elif self.status == self.PICKED:
            self.shelf = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.recipient_name} ({self.status})"


class AppSettings(models.Model):
    """
    Singleton model for application settings
    """
    printer_ip = models.CharField(max_length=15, default='192.168.10.172', help_text='Printer IP address')
    printer_port = models.IntegerField(default=9100, help_text='Printer port')
    enable_qr_codes = models.BooleanField(default=True, help_text='Enable QR code generation on receipts')
    default_package_type = models.CharField(max_length=10, choices=Package.TYPE_CHOICES, default=Package.PACKAGE)
    auto_print_on_create = models.BooleanField(default=True, help_text='Automatically print receipt when package is created')
    enable_reprint = models.BooleanField(default=True, help_text='Allow reprinting of package receipts')
    max_reprint_attempts = models.IntegerField(default=3, help_text='Maximum number of reprint attempts')
    notification_email = models.EmailField(blank=True, null=True, help_text='Email for notifications')
    enable_sms_notifications = models.BooleanField(default=False, help_text='Enable SMS notifications for package updates')
    sms_api_key = models.CharField(max_length=255, blank=True, null=True, help_text='SMS API key')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and AppSettings.objects.exists():
            raise ValueError("Only one AppSettings instance is allowed.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get the singleton settings instance, creating if doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1, defaults={
            'printer_ip': '192.168.10.172',
            'printer_port': 9100,
            'enable_qr_codes': True,
            'default_package_type': Package.PACKAGE,
            'auto_print_on_create': True,
            'enable_reprint': True,
            'max_reprint_attempts': 3,
        })
        return settings

    def __str__(self):
        return "Application Settings"


class PackageHistory(models.Model):
    """
    Track package status changes and actions
    """
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50, help_text='Action performed (created, picked, reprinted, etc.)')
    old_status = models.CharField(max_length=10, choices=Package.STATUS_CHOICES, blank=True, null=True)
    new_status = models.CharField(max_length=10, choices=Package.STATUS_CHOICES, blank=True, null=True)
    performed_by = models.CharField(max_length=100, blank=True, null=True, help_text='User who performed the action')
    notes = models.TextField(blank=True, null=True, help_text='Additional notes')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Package History'
        verbose_name_plural = 'Package History'

    def __str__(self):
        return f"{self.package.code} - {self.action} at {self.timestamp}"
