from django.urls import path
from .views import (
    SecurityKeyListView,
    SecurityKeyDetailView,
    CheckoutKeyView,
    ReturnKeyView,
    PhoneExtensionListCreateView,
    PhoneExtensionDetailView,
    ReportedIssueListCreateView,
    ReportedIssueDetailView,
    SecurityKeyHistoryView,
    UpdateIssueStatusView
)


urlpatterns = [
    # Security Keys
    path('security-keys/', SecurityKeyListView.as_view(), name='security-key-list'),
    path('security-keys/<int:pk>/history/', SecurityKeyHistoryView.as_view(), name='key-history'),

    path('security-keys/<int:pk>/', SecurityKeyDetailView.as_view(), name='security-key-detail'),
    path('security-keys/<int:pk>/checkout/', CheckoutKeyView.as_view(), name='checkout-key'),
    path('security-keys/<int:pk>/return/', ReturnKeyView.as_view(), name='return-key'),
    
    # Phone Extensions
    path('phone-extensions/', PhoneExtensionListCreateView.as_view(), name='phone-extension-list'),
    path('phone-extensions/<int:pk>/', PhoneExtensionDetailView.as_view(), name='phone-extension-detail'),
    
    # Reported Issues
    path('issues/', ReportedIssueListCreateView.as_view(), name='issue-list'),
    path('issues/<int:pk>/', ReportedIssueDetailView.as_view(), name='issue-detail'),
    path('issues/<int:pk>/status/', UpdateIssueStatusView.as_view(), name='update-issue-status'),
]