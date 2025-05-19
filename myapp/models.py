from django.db import models
from django.utils import timezone
import random
import string

def generate_package_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Package.objects.filter(code=code).exists():
            return code

def get_lowest_unoccupied_shelf():
    occupied = set(
        Package.objects.filter(status=Package.PENDING)
        .values_list('shelf', flat=True)
    )
    for i in range(1, 100): 
        shelf = f"S{i}"
        if shelf not in occupied:
            return shelf
    return None  

class Package(models.Model):
    PACKAGE = 'package'
    DOCUMENT = 'document'
    KEYS='keys'
    TYPE_CHOICES = [
        (PACKAGE, 'Package'),
        (DOCUMENT, 'Document'),
        (KEYS,'keys'),
    ]
    
    PENDING = 'pending'
    PICKED = 'picked'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PICKED, 'Picked'),
    ]
    
    code = models.CharField(max_length=8, default=generate_package_code, unique=True, editable=False)
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
    picked_at = models.DateTimeField(blank=True, null=True)

    shelf = models.CharField(max_length=10, blank=True, null=True, editable=False)

    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.status == self.PENDING and not self.shelf:
            self.shelf = get_lowest_unoccupied_shelf()
        elif self.status == self.PICKED:
            self.shelf = None  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.recipient_name} ({self.status})"
