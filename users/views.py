from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from .models import User, EventLog
from .serializers import UserSerializer, AdminUserSerializer, LoginSerializer
from .permissions import IsAdmin, IsStaff, IsReception, IsOwnerOrAdmin
from rest_framework import generics
from .models import EventLog
from .serializers import EventLogSerializer

class EventLogListView(generics.ListAPIView):
    queryset = EventLog.objects.all().order_by('-timestamp')
    serializer_class = EventLogSerializer
    permission_classes = [IsAdmin]
    
class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    
    def get_serializer_class(self):
        if self.request.user.is_admin():
            return AdminUserSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Log the user creation event
        EventLog.objects.create(
            user=request.user,
            action=EventLog.ActionTypes.CREATE,
            object_type='User',
            object_id=response.data.get('id'),
            metadata={
                'created_user': response.data.get('username'),
                'role': response.data.get('role')
            }
        )
        return response

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        if self.request.user.is_admin():
            return AdminUserSerializer
        return UserSerializer
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        # Log the user update event
        EventLog.objects.create(
            user=request.user,
            action=EventLog.ActionTypes.UPDATE,
            object_type='User',
            object_id=self.get_object().id,
            metadata={
                'updated_fields': request.data
            }
        )
        return response
    
    def destroy(self, request, *args, **kwargs):
        user_to_delete = self.get_object()
        
        # Log the user deletion event before deletion
        EventLog.objects.create(
            user=request.user,
            action=EventLog.ActionTypes.DELETE,
            object_type='User',
            object_id=user_to_delete.id,
            metadata={
                'deleted_user': user_to_delete.username
            }
        )
        return super().destroy(request, *args, **kwargs)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Log the login event
        EventLog.objects.create(
            user=user,
            action=EventLog.ActionTypes.LOGIN,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log the logout event before logging out
            EventLog.objects.create(
                user=request.user,
                action=EventLog.ActionTypes.LOGOUT,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logout(request)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')