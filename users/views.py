from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from .serializers import MyTokenSerializer, UserSerializer
from .models import User
from .permissions import IsAdminRole, IsStaffOrAdmin


class MyTokenView(TokenObtainPairView):
    serializer_class = MyTokenSerializer

class CitizenCreateListView(ListCreateAPIView):
    """Create new citizen account"""
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all().filter(role=User.Role.CITIZEN)

    def get_permissions(self):
        if self.request.method == 'POST':
            # allow anyone to create an account
            return [AllowAny()]
        return [IsStaffOrAdmin()]
    
    def perform_create(self, serializer):
        return serializer.save(role=User.Role.CITIZEN)


class StaffCreateListView(ListCreateAPIView):
    """Admin-only: list all staff members and create new ones"""
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return User.objects.all().filter(role=User.Role.STAFF)
    
    def perform_create(self, serializer):
        return serializer.save(role=User.Role.STAFF)

    

class AdminCreateListView(ListCreateAPIView):
    """Admin-only: list all admin members and create new ones"""
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return User.objects.all().filter(role=User.Role.ADMIN)
    
    def perform_create(self, serializer):
        return serializer.save(role=User.Role.ADMIN)

    
class UserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """Retrieve update or destroy a user instance"""
    queryset = User.objects.all()
    serializer_class = UserSerializer