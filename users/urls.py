from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import StaffCreateListView, AdminCreateListView, UserRetrieveUpdateDestroyAPIView, CitizenCreateListView, MyTokenView


urlpatterns = [
    path('staff/', StaffCreateListView.as_view(), name='staff_list_create'),
    path('admin/', AdminCreateListView.as_view(), name='admin_list_create'),
    path('citizen/', CitizenCreateListView.as_view(), name='citizen_list_create'),
    path('<int:pk>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user_retrieve_update_delete'),
    path('token/', MyTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), )
]