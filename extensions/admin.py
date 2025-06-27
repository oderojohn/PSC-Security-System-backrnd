from django.contrib import admin
from .models import PhoneExtension, ReportedIssue, SecurityKey

admin.site.register(PhoneExtension)
admin.site.register(ReportedIssue)
admin.site.register(SecurityKey)