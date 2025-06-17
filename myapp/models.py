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
    recipient_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    dropped_by = models.CharField(max_length=100)
    dropper_phone = models.CharField(max_length=20)

    picked_by = models.CharField(max_length=100, blank=True, null=True)
    picker_phone = models.CharField(max_length=20, blank=True, null=True)
    picker_id = models.CharField(max_length=20, blank=True, null=True)
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
