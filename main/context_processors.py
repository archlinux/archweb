def secure(request):
    return {'secure': request.is_secure()}

# vim: set ts=4 sw=4 et:
