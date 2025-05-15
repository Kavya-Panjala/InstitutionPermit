from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Event, User, Notification, Attendance
from datetime import datetime

events_bp = Blueprint('events', __name__)

@events_bp.route('/events')
@login_required
def list_events():
    if current_user.role == 'student':
        # Show events created by the student and all approved events
        created_events = Event.query.filter_by(user_id=current_user.id).all()
        approved_events = Event.query.filter_by(status='approved', department=current_user.department).all()
        
        # Combine and remove duplicates
        events = list(set(created_events + approved_events))
    elif current_user.role == 'hod':
        # Show events for the HOD's department
        events = Event.query.filter_by(department=current_user.department).all()
    else:  # Security guard
        # Show all approved events
        events = Event.query.filter_by(status='approved').all()
        
    return render_template('event_list.html', events=events)

@events_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role != 'student':
        flash('Only students can create events', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        
        if not all([title, description, location, start_date, start_time, end_date, end_time]):
            flash('Please fill in all required fields', 'danger')
            return render_template('create_event.html')
            
        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            
            if start_datetime >= end_datetime:
                flash('End time must be after start time', 'danger')
                return render_template('create_event.html')
                
            new_event = Event(
                title=title,
                description=description,
                location=location,
                start_time=start_datetime,
                end_time=end_datetime,
                department=current_user.department,
                user_id=current_user.id
            )
            
            db.session.add(new_event)
            db.session.commit()
            
            # Notify HODs of the department
            hods = User.query.filter_by(role='hod', department=current_user.department).all()
            for hod in hods:
                notification = Notification(
                    user_id=hod.id,
                    title='New Event Request',
                    message=f'A new event "{title}" has been requested by {current_user.first_name} {current_user.last_name}',
                    related_to='event',
                    reference_id=new_event.id
                )
                db.session.add(notification)
                
            db.session.commit()
            
            flash('Event created successfully and awaiting approval', 'success')
            return redirect(url_for('events.view_event', event_id=new_event.id))
            
        except Exception as e:
            flash(f'Error creating event: {str(e)}', 'danger')
            return render_template('create_event.html')
            
    return render_template('create_event.html')

@events_bp.route('/events/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check permissions
    if current_user.role == 'student' and event.user_id != current_user.id and event.status != 'approved':
        flash('You do not have permission to view this event', 'danger')
        return redirect(url_for('events.list_events'))
        
    # Get the creator's name
    creator = User.query.get(event.user_id)
    
    # Get approver's name if approved
    approver = None
    if event.approved_by:
        approver = User.query.get(event.approved_by)
        
    # Get attendance for this event
    attendance = None
    if current_user.role == 'student':
        attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            event_id=event.id
        ).first()
        
    # Get all attendees for HOD or event creator
    attendees = []
    if current_user.role == 'hod' or event.user_id == current_user.id:
        attendees = Attendance.query.filter_by(event_id=event.id).all()
        # Get user details for each attendance record
        for record in attendees:
            record.user_details = User.query.get(record.user_id)
    
    return render_template(
        'event_details.html', 
        event=event, 
        creator=creator, 
        approver=approver, 
        attendance=attendance,
        attendees=attendees
    )

@events_bp.route('/events/<int:event_id>/approve', methods=['POST'])
@login_required
def approve_event(event_id):
    if current_user.role != 'hod':
        flash('Only HODs can approve events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    event = Event.query.get_or_404(event_id)
    
    if event.department != current_user.department:
        flash('You can only approve events for your department', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    reason = request.form.get('reason', '')
    decision = request.form.get('decision')
    
    if decision == 'approve':
        event.status = 'approved'
        event.approved_by = current_user.id
        event.reason = reason or 'Approved by department HOD'
        
        # Notify the event creator
        notification = Notification(
            user_id=event.user_id,
            title='Event Approved',
            message=f'Your event "{event.title}" has been approved' + (f' with comment: {reason}' if reason else ''),
            related_to='event',
            reference_id=event.id
        )
        db.session.add(notification)
        
        # Notify security guards
        security_guards = User.query.filter_by(role='security').all()
        for guard in security_guards:
            notification = Notification(
                user_id=guard.id,
                title='New Approved Event',
                message=f'Event "{event.title}" has been approved for {event.start_time.strftime("%Y-%m-%d %H:%M")}',
                related_to='event',
                reference_id=event.id
            )
            db.session.add(notification)
            
        flash('Event approved successfully', 'success')
        
    elif decision == 'reject':
        if not reason:
            flash('Please provide a reason for rejection', 'danger')
            return redirect(url_for('events.view_event', event_id=event_id))
            
        event.status = 'rejected'
        event.reason = reason
        
        # Notify the event creator
        notification = Notification(
            user_id=event.user_id,
            title='Event Rejected',
            message=f'Your event "{event.title}" has been rejected with reason: {reason}',
            related_to='event',
            reference_id=event.id
        )
        db.session.add(notification)
        
        flash('Event rejected', 'warning')
        
    db.session.commit()
    return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    if current_user.role != 'student':
        flash('Only students can register for events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    event = Event.query.get_or_404(event_id)
    
    if event.status != 'approved':
        flash('You can only register for approved events', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Check if already registered
    existing_registration = Attendance.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this event', 'info')
    else:
        # Register for the event
        attendance = Attendance(
            user_id=current_user.id,
            event_id=event.id,
            status='registered'
        )
        db.session.add(attendance)
        
        # Notify event creator
        notification = Notification(
            user_id=event.user_id,
            title='New Event Registration',
            message=f'{current_user.first_name} {current_user.last_name} has registered for your event "{event.title}"',
            related_to='event',
            reference_id=event.id
        )
        db.session.add(notification)
        
        db.session.commit()
        flash('Successfully registered for the event', 'success')
        
    return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route('/events/<int:event_id>/cancel-registration', methods=['POST'])
@login_required
def cancel_event_registration(event_id):
    if current_user.role != 'student':
        flash('Only students can cancel event registrations', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    event = Event.query.get_or_404(event_id)
    
    # Check if registered
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()
    
    if not attendance:
        flash('You are not registered for this event', 'warning')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Cannot cancel if already attended
    if attendance.status == 'attended':
        flash('Cannot cancel registration after attendance has been marked', 'danger')
        return redirect(url_for('events.view_event', event_id=event_id))
        
    # Delete attendance record
    db.session.delete(attendance)
    
    # Notify event creator
    notification = Notification(
        user_id=event.user_id,
        title='Event Registration Cancelled',
        message=f'{current_user.first_name} {current_user.last_name} has cancelled registration for your event "{event.title}"',
        related_to='event',
        reference_id=event.id
    )
    db.session.add(notification)
    
    db.session.commit()
    flash('Event registration cancelled', 'info')
    return redirect(url_for('events.view_event', event_id=event_id))
