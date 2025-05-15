from datetime import datetime
from flask import flash, redirect, url_for
from flask_login import current_user
from functools import wraps

def role_required(*roles):
    """
    Decorator to restrict route access based on user role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def format_datetime(dt):
    """Format datetime object to readable string"""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")

def timesince(dt, default="just now"):
    """
    Returns a human-friendly time difference string (e.g. "3 minutes ago", "1 day ago")
    """
    if dt is None:
        return default
        
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 10:
        return "just now"
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{int(hours)} hour{'s' if hours != 1 else ''} ago"
    if seconds < 604800:
        days = seconds // 86400
        return f"{int(days)} day{'s' if days != 1 else ''} ago"
    if seconds < 2592000:
        weeks = seconds // 604800
        return f"{int(weeks)} week{'s' if weeks != 1 else ''} ago"
    if seconds < 31536000:
        months = seconds // 2592000
        return f"{int(months)} month{'s' if months != 1 else ''} ago"
    
    years = seconds // 31536000
    return f"{int(years)} year{'s' if years != 1 else ''} ago"

def get_status_badge_class(status):
    """Return the appropriate Bootstrap badge class based on status"""
    status_classes = {
        'pending': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'completed': 'bg-info',
        'attended': 'bg-success',
        'absent': 'bg-danger',
        'registered': 'bg-primary'
    }
    return status_classes.get(status, 'bg-secondary')

def is_active_now(start_time, end_time):
    """Check if the event/outpass is currently active"""
    now = datetime.utcnow()
    return start_time <= now <= end_time
