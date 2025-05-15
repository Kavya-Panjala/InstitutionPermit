from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Event, Attendance, User, Notification
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance/<int:event_id>')
@login_required
def view_attendance(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check permissions
    if current_user.role == 'student' and event.user_id != current_user.id:
        flash('Only event organizers can view attendance', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    if current_user.role == 'hod' and event.department != current_user.department:
        flash('You can only view attendance for events in your department', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Get all attendance records for this event
    attendance_records = Attendance.query.filter_by(event_id=event_id).all()
    
    # Get user details for each attendance record
    for record in attendance_records:
        record.user_details = User.query.get(record.user_id)
        
    # Calculate statistics
    total_registrations = len(attendance_records)
    total_attended = sum(1 for r in attendance_records if r.status == 'attended')
    total_absent = sum(1 for r in attendance_records if r.status == 'absent')
    attendance_rate = (total_attended / total_registrations * 100) if total_registrations > 0 else 0
    
    stats = {
        'total_registrations': total_registrations,
        'total_attended': total_attended,
        'total_absent': total_absent,
        'attendance_rate': round(attendance_rate, 2)
    }
    
    return render_template(
        'attendance.html',
        event=event,
        attendance_records=attendance_records,
        stats=stats
    )

@attendance_bp.route('/attendance/<int:event_id>/mark', methods=['POST'])
@login_required
def mark_attendance(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Only HODs and event organizers can mark attendance
    if current_user.role == 'student' and event.user_id != current_user.id:
        flash('Only event organizers and HODs can mark attendance', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    if current_user.role == 'hod' and event.department != current_user.department:
        flash('You can only mark attendance for events in your department', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    user_id = request.form.get('user_id', type=int)
    attendance_status = request.form.get('status')
    
    if not user_id or not attendance_status or attendance_status not in ['attended', 'absent']:
        flash('Invalid attendance data', 'danger')
        return redirect(url_for('attendance.view_attendance', event_id=event_id))
        
    # Find the attendance record
    attendance = Attendance.query.filter_by(
        user_id=user_id,
        event_id=event_id
    ).first()
    
    if not attendance:
        flash('Attendance record not found', 'danger')
        return redirect(url_for('attendance.view_attendance', event_id=event_id))
        
    # Update attendance status
    attendance.status = attendance_status
    
    if attendance_status == 'attended':
        attendance.check_in_time = datetime.utcnow()
    
    db.session.commit()
    
    student = User.query.get(user_id)
    flash(f'Attendance marked as {attendance_status} for {student.first_name} {student.last_name}', 'success')
    return redirect(url_for('attendance.view_attendance', event_id=event_id))

@attendance_bp.route('/attendance/<int:event_id>/check-in', methods=['POST'])
@login_required
def check_in(event_id):
    if current_user.role != 'student':
        flash('Only students can check in to events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    event = Event.query.get_or_404(event_id)
    
    if event.status != 'approved':
        flash('Can only check in to approved events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Find the attendance record
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not attendance:
        # Create a new attendance record if not registered
        attendance = Attendance(
            user_id=current_user.id,
            event_id=event_id,
            status='registered'
        )
        db.session.add(attendance)
        
    # Check if already checked in
    if attendance.status == 'attended':
        flash('You have already checked in to this event', 'info')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Update attendance status
    attendance.status = 'attended'
    attendance.check_in_time = datetime.utcnow()
    
    # Notify event creator
    notification = Notification(
        user_id=event.user_id,
        title='Event Check-in',
        message=f'{current_user.first_name} {current_user.last_name} has checked in to your event "{event.title}"',
        related_to='event',
        reference_id=event.id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    flash('Successfully checked in to the event', 'success')
    return redirect(url_for('events.view_event', event_id=event_id))

@attendance_bp.route('/attendance/<int:event_id>/check-out', methods=['POST'])
@login_required
def check_out(event_id):
    if current_user.role != 'student':
        flash('Only students can check out from events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    event = Event.query.get_or_404(event_id)
    
    # Find the attendance record
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not attendance or attendance.status != 'attended':
        flash('You have not checked in to this event', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Update check-out time
    attendance.check_out_time = datetime.utcnow()
    
    db.session.commit()
    
    flash('Successfully checked out from the event', 'success')
    return redirect(url_for('events.view_event', event_id=event_id))

@attendance_bp.route('/attendance/export/<int:event_id>')
@login_required
def export_attendance(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check permissions
    if current_user.role == 'student' and event.user_id != current_user.id:
        flash('Only event organizers and HODs can export attendance', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    if current_user.role == 'hod' and event.department != current_user.department:
        flash('You can only export attendance for events in your department', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Get all attendance records for this event
    attendance_records = Attendance.query.filter_by(event_id=event_id).all()
    
    # Get user details for each attendance record
    for record in attendance_records:
        record.user_details = User.query.get(record.user_id)
        
    return render_template(
        'attendance_export.html',
        event=event,
        attendance_records=attendance_records
    )
