from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PackageViewSet, AppSettingsViewSet

router = DefaultRouter()
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'settings', AppSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]