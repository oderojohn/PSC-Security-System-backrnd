#  for event logs. record every event done by any user in the system 
from django.utils.deprecation import MiddlewareMixin
from .models import EventLog
import json

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip logging for certain paths
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
            
        if request.user.is_authenticated:
            action = self._determine_action(request)
            
            EventLog.objects.create(
                user=request.user,
                action=action,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'data': self._get_safe_request_data(request)
                }
            )
    
    def _determine_action(self, request):
        if request.path == '/api/auth/login/':
            return EventLog.ActionTypes.LOGIN
        elif request.path == '/api/auth/logout/':
            return EventLog.ActionTypes.LOGOUT
        elif request.method == 'POST':
            return EventLog.ActionTypes.CREATE
        elif request.method == 'PUT' or request.method == 'PATCH':
            return EventLog.ActionTypes.UPDATE
        elif request.method == 'DELETE':
            return EventLog.ActionTypes.DELETE
        else:
            return EventLog.ActionTypes.ACCESS
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    def _get_safe_request_data(self, request):
        try:
            if request.body:
                data = json.loads(request.body)
                # Redact sensitive fields
                for field in ['password', 'token', 'secret']:
                    if field in data:
                        data[field] = '*****'
                return data
        except:
            return {}
        return {}