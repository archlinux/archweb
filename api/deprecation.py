from functools import wraps


def deprecated_json_endpoint(successor_path: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            response['Deprecation'] = 'true'
            response['Link'] = f'<{successor_path}>; rel="successor-version"'
            return response
        return wrapper
    return decorator
