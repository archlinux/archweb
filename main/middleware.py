import threading

user_holder = threading.local()
user_holder.user = None

# http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
class AutoUserMiddleware(object):
    '''Saves the current user so it can be retrieved by the admin'''
    def process_request(self, request):
        user_holder.user = request.user


def get_user():
    '''Get the currently logged in request.user'''
    return user_holder.user

