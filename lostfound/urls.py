from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LostItemViewSet, FoundItemViewSet ,PickupLogViewSet


router = DefaultRouter()
router.register(r'lost', LostItemViewSet, basename='lost')
router.register(r'found', FoundItemViewSet, basename='found')
router.register(r'pickuplogs', PickupLogViewSet, basename='pickuplog')

urlpatterns = [
    path('', include(router.urls)),
    #path('stats/', ItemStatsView.as_view({'get': 'list'}), name='item-stats'),
]
