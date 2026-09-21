from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def staff_only(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped

def require_model_permission(user, model, action):
    opts = model._meta
    if not user.has_perm(f'{opts.app_label}.{action}_{opts.model_name}'):
        raise PermissionDenied
