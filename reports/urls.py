from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reports.views import ReportViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [    
    path('', include(router.urls)),
]