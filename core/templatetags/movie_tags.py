from django import template
from dashboard.models import ViewingHistory

register = template.Library()

@register.filter(name='get_watch_progress')
def get_watch_progress(movie, user):
    if not user:
        return 0
    try:

        if hasattr(user, 'user_id'):
            history = ViewingHistory.objects.filter(user=user, movie=movie).first()
            if history:
                return float(history.progress)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Error in get_watch_progress: %s", e)
        pass
    return 0

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0