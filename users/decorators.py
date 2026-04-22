from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from users.models import User

def login_required_custom(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        u_id = request.session.get('user_id')
        if not u_id:
            messages.error(request, "Please login to access this page.")
            return redirect('users:login')

        user = User.objects.filter(user_id=u_id).first()
        if not user:
            request.session.flush()
            messages.error(request, "Session invalid. Please login again.")
            return redirect('users:login')

        request.current_user = user
        return view_func(request, *args, **kwargs)
    return _wrapped_view