from django.contrib.auth.views import logout_then_login, login
from django.conf import settings
    
class SiteLogin:
    def __init__(self):
        self.login_path = settings.LOGIN_URL
    def process_request(self, request):
        if request.user.is_anonymous() and request.path != self.login_path:
            if request.POST:
                return login(request)
            else:
                return HttpResponseRedirect('%s?next=%s' % (self.login_path, request.path))

