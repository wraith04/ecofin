from django.conf import settings
from django.contrib.auth import logout
from datetime import datetime, timedelta

class SessionIdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 只对认证用户检查
        if request.user.is_authenticated:
            now = datetime.now()
            if 'last_activity' in request.session:
                last_activity = datetime.strptime(request.session['last_activity'], "%Y-%m-%d %H:%M:%S")
                if now - last_activity > timedelta(seconds=settings.SESSION_IDLE_TIMEOUT):
                    logout(request)
            request.session['last_activity'] = now.strftime("%Y-%m-%d %H:%M:%S")
        response = self.get_response(request)
        return response
