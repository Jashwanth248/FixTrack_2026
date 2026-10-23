import time
from django.contrib.auth import logout

class IdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()
            last = request.session.get('last_activity', now)
            if now - last >= 1800:
                logout(request)
            else:
                request.session['last_activity'] = now
        return self.get_response(request)
