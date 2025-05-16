from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import Event, OutPass, User, Notification, Attendance
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role == 'student':
        return redirect(url_for('dashboard.student_dashboard'))
    elif current_user.role == 'hod':
        return redirect(url_for('dashboard.hod_dashboard'))
    return redirect(url_for('dashboard.student_dashboard'))  # Default fallback

@dashboard_bp.route('/dashboard/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('dashboard.index'))
        
    # Get pending events
    pending_events = Event.query.filter_by(
        user_id=current_user.id, 
        status='pending'
    ).order_by(Event.created_at.desc()).limit(5).all()
    
    # Get upcoming approved events (registered for or created by the student)
    attended_event_ids = [
        a.event_id for a in Attendance.query.filter_by(user_id=current_user.id).all()
    ]
    upcoming_events = Event.query.filter(
        (Event.status == 'approved') &
        (Event.end_time > datetime.utcnow()) &
        ((Event.user_id == current_user.id) | (Event.id.in_(attended_event_ids)))
    ).order_by(Event.start_time).limit(5).all()
    
    # Get pending and approved outpasses
    pending_outpasses = OutPass.query.filter_by(
        user_id=current_user.id, 
        status='pending'
    ).order_by(OutPass.created_at.desc()).limit(3).all()
    
    active_outpasses = OutPass.query.filter(
        OutPass.user_id == current_user.id,
        OutPass.status == 'approved',
        OutPass.start_time <= datetime.utcnow(),
        OutPass.end_time >= datetime.utcnow()
    ).all()
    
    upcoming_outpasses = OutPass.query.filter(
        OutPass.user_id == current_user.id,
        OutPass.status == 'approved',
        OutPass.start_time > datetime.utcnow()
    ).order_by(OutPass.start_time).limit(3).all()
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Stats
    total_events_created = Event.query.filter_by(user_id=current_user.id).count()
    total_events_approved = Event.query.filter_by(user_id=current_user.id, status='approved').count()
    total_outpasses = OutPass.query.filter_by(user_id=current_user.id).count()
    total_outpasses_approved = OutPass.query.filter_by(user_id=current_user.id, status='approved').count()
    
    return render_template(
        'dashboard.html',
        pending_events=pending_events,
        upcoming_events=upcoming_events,
        pending_outpasses=pending_outpasses,
        active_outpasses=active_outpasses,
        upcoming_outpasses=upcoming_outpasses,
        unread_notifications=unread_notifications,
        total_events_created=total_events_created,
        total_events_approved=total_events_approved,
        total_outpasses=total_outpasses,
        total_outpasses_approved=total_outpasses_approved
    )

@dashboard_bp.route('/dashboard/hod')
@login_required
def hod_dashboard():
    if current_user.role != 'hod':
        return redirect(url_for('dashboard.index'))
        
    # Get pending events for this department
    pending_events = Event.query.filter_by(
        department=current_user.department, 
        status='pending'
    ).order_by(Event.created_at.desc()).limit(5).all()
    
    # Get upcoming approved events for this department
    upcoming_events = Event.query.filter(
        Event.department == current_user.department,
        Event.status == 'approved',
        Event.end_time > datetime.utcnow()
    ).order_by(Event.start_time).limit(5).all()
    
    # Get pending outpasses for students in this department
    students = User.query.filter_by(department=current_user.department, role='student').all()
    student_ids = [student.id for student in students]
    
    pending_outpasses = OutPass.query.filter(
        OutPass.user_id.in_(student_ids),
        OutPass.status == 'pending'
    ).order_by(OutPass.created_at.desc()).limit(5).all()
    
    # Map student IDs to names for display
    student_map = {student.id: f"{student.first_name} {student.last_name}" for student in students}
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Stats for charts
    # Events by status
    event_stats = db.session.query(
        Event.status, 
        func.count(Event.id)
    ).filter(
        Event.department == current_user.department
    ).group_by(Event.status).all()
    
    event_stats_dict = {status: count for status, count in event_stats}
    
    # Outpasses by status
    outpass_stats = db.session.query(
        OutPass.status, 
        func.count(OutPass.id)
    ).filter(
        OutPass.user_id.in_(student_ids)
    ).group_by(OutPass.status).all()
    
    outpass_stats_dict = {status: count for status, count in outpass_stats}
    
    # Events by day of week
    today = datetime.utcnow().date()
    start_of_month = today.replace(day=1)
    
    events_by_day = db.session.query(
        func.extract('dow', Event.start_time).label('day_of_week'), 
        func.count(Event.id)
    ).filter(
        Event.department == current_user.department,
        Event.start_time >= start_of_month
    ).group_by('day_of_week').all()
    
    # PostgreSQL's extract(dow) returns 0 for Sunday, 1 for Monday, etc.
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    events_by_day_dict = {days[int(day)]: count for day, count in events_by_day}
    
    return render_template(
        'hod_dashboard.html',
        pending_events=pending_events,
        upcoming_events=upcoming_events,
        pending_outpasses=pending_outpasses,
        student_map=student_map,
        unread_notifications=unread_notifications,
        event_stats=event_stats_dict,
        outpass_stats=outpass_stats_dict,
        events_by_day=events_by_day_dict
    )



@dashboard_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    # Mark all as read
    for notification in notifications:
        notification.is_read = True
        
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)
