# models.py
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class PhoneExtension(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.number})"

# models.py
class ReportedIssue(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('Facilities', 'Facilities'),
        ('Maintenance', 'Maintenance'),
        ('Security', 'Security'),
        ('IT', 'IT'),
        ('Other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='General')
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

class SecurityKey(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('checked-out', 'Checked Out'),
        ('lost', 'Lost'),
    ]

    HOLDER_TYPES = [
        ('staff', 'Staff'),
        ('member', 'Member'),
        ('contractor', 'Contractor'),
        ('visitor', 'Visitor'),
    ]

    KEY_TYPES = [
        ('Master', 'Master'),
        ('Access', 'Access'),
        ('Other', 'Other'),
    ]

    key_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100)
    key_type = models.CharField(max_length=20, choices=KEY_TYPES, default='Access')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    current_holder_name = models.CharField(max_length=100, blank=True, null=True)
    current_holder_type = models.CharField(max_length=20, choices=HOLDER_TYPES, blank=True, null=True)
    current_holder_phone = models.CharField(max_length=20, blank=True, null=True)
    checkout_time = models.DateTimeField(blank=True, null=True)
    return_time = models.DateTimeField(blank=True, null=True)


class KeyHistory(models.Model):
    key = models.ForeignKey(SecurityKey, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20)  # 'checkout' or 'return'
    holder_name = models.CharField(max_length=100)
    holder_type = models.CharField(max_length=20)
    holder_phone = models.CharField(max_length=20, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Who performed the action
    notes = models.TextField(blank=True)
