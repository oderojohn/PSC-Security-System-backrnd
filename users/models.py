from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STAFF = 'STAFF', 'Staff'
        RECEPTION = 'RECEPTION', 'Reception'
        MEMBER = 'MEMBER', 'Member'

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.MEMBER)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_staff_member(self):
        return self.role in [self.Role.ADMIN, self.Role.STAFF]
    
    def is_reception(self):
        return self.role == self.Role.RECEPTION


class EventLog(models.Model):
    class ActionTypes(models.TextChoices):
        LOGIN = 'LOGIN', 'User Login'
        LOGOUT = 'LOGOUT', 'User Logout'
        CREATE = 'CREATE', 'Create Operation'
        UPDATE = 'UPDATE', 'Update Operation'
        DELETE = 'DELETE', 'Delete Operation'
        ACCESS = 'ACCESS', 'Access Operation'
        SYSTEM = 'SYSTEM', 'System Event'
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ActionTypes.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    object_type = models.CharField(max_length=100, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.get_action_display()} at {self.timestamp}"
