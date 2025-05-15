from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import OutPass, User, Notification
from datetime import datetime

outpass_bp = Blueprint('outpass', __name__)

@outpass_bp.route('/outpass')
@login_required
def list_outpasses():
    if current_user.role == 'student':
        # Students see their own outpasses
        outpasses = OutPass.query.filter_by(user_id=current_user.id).order_by(OutPass.created_at.desc()).all()
    elif current_user.role == 'hod':
        # HODs see outpasses for their department
        students = User.query.filter_by(department=current_user.department, role='student').all()
        student_ids = [student.id for student in students]
        outpasses = OutPass.query.filter(OutPass.user_id.in_(student_ids)).order_by(OutPass.created_at.desc()).all()
    else:  # Security guard
        # Security guards see all approved outpasses
        outpasses = OutPass.query.filter_by(status='approved').order_by(OutPass.created_at.desc()).all()
        
    return render_template('outpass_list.html', outpasses=outpasses)

@outpass_bp.route('/outpass/request', methods=['GET', 'POST'])
@login_required
def request_outpass():
    if current_user.role != 'student':
        flash('Only students can request out passes', 'danger')
        return redirect(url_for('outpass.list_outpasses'))
        
    if request.method == 'POST':
        reason = request.form.get('reason')
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        
        if not all([reason, start_date, start_time, end_date, end_time]):
            flash('Please fill in all required fields', 'danger')
            return render_template('outpass_request.html')
            
        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            
            if start_datetime >= end_datetime:
                flash('End time must be after start time', 'danger')
                return render_template('outpass_request.html')
                
            # Check if there is an overlapping approved outpass
            overlapping_outpasses = OutPass.query.filter(
                OutPass.user_id == current_user.id,
                OutPass.status == 'approved',
                OutPass.start_time <= end_datetime,
                OutPass.end_time >= start_datetime
            ).all()
            
            if overlapping_outpasses:
                flash('You already have an approved outpass during this time period', 'danger')
                return render_template('outpass_request.html')
                
            new_outpass = OutPass(
                user_id=current_user.id,
                reason=reason,
                start_time=start_datetime,
                end_time=end_datetime
            )
            
            db.session.add(new_outpass)
            db.session.commit()
            
            # Notify HODs of the department
            hods = User.query.filter_by(role='hod', department=current_user.department).all()
            for hod in hods:
                notification = Notification(
                    user_id=hod.id,
                    title='New Out Pass Request',
                    message=f'{current_user.first_name} {current_user.last_name} has requested an out pass from {start_datetime.strftime("%Y-%m-%d %H:%M")} to {end_datetime.strftime("%Y-%m-%d %H:%M")}',
                    related_to='outpass',
                    reference_id=new_outpass.id
                )
                db.session.add(notification)
                
            db.session.commit()
            
            flash('Out pass requested successfully and awaiting approval', 'success')
            return redirect(url_for('outpass.view_outpass', outpass_id=new_outpass.id))
            
        except Exception as e:
            flash(f'Error requesting out pass: {str(e)}', 'danger')
            return render_template('outpass_request.html')
            
    return render_template('outpass_request.html')

@outpass_bp.route('/outpass/<int:outpass_id>')
@login_required
def view_outpass(outpass_id):
    outpass = OutPass.query.get_or_404(outpass_id)
    
    # Check permissions
    if current_user.role == 'student' and outpass.user_id != current_user.id:
        flash('You do not have permission to view this out pass', 'danger')
        return redirect(url_for('outpass.list_outpasses'))
        
    if current_user.role == 'hod':
        student = User.query.get(outpass.user_id)
        if student.department != current_user.department:
            flash('You can only view out passes for students in your department', 'danger')
            return redirect(url_for('outpass.list_outpasses'))
            
    # Get student's details
    student = User.query.get(outpass.user_id)
    
    # Get approver's details if approved
    approver = None
    if outpass.approved_by:
        approver = User.query.get(outpass.approved_by)
        
    return render_template(
        'outpass_details.html', 
        outpass=outpass, 
        student=student, 
        approver=approver
    )

@outpass_bp.route('/outpass/<int:outpass_id>/approve', methods=['POST'])
@login_required
def approve_outpass(outpass_id):
    if current_user.role != 'hod':
        flash('Only HODs can approve out passes', 'danger')
        return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))
        
    outpass = OutPass.query.get_or_404(outpass_id)
    student = User.query.get(outpass.user_id)
    
    if student.department != current_user.department:
        flash('You can only approve out passes for students in your department', 'danger')
        return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))
        
    comment = request.form.get('comment', '')
    decision = request.form.get('decision')
    
    if decision == 'approve':
        outpass.status = 'approved'
        outpass.approved_by = current_user.id
        outpass.approval_comment = comment or 'Approved by department HOD'
        
        # Notify the student
        notification = Notification(
            user_id=outpass.user_id,
            title='Out Pass Approved',
            message=f'Your out pass request for {outpass.start_time.strftime("%Y-%m-%d %H:%M")} to {outpass.end_time.strftime("%Y-%m-%d %H:%M")} has been approved' + (f' with comment: {comment}' if comment else ''),
            related_to='outpass',
            reference_id=outpass.id
        )
        db.session.add(notification)
        
        # Notify security guards
        security_guards = User.query.filter_by(role='security').all()
        for guard in security_guards:
            notification = Notification(
                user_id=guard.id,
                title='New Approved Out Pass',
                message=f'Out pass for {student.first_name} {student.last_name} has been approved from {outpass.start_time.strftime("%Y-%m-%d %H:%M")} to {outpass.end_time.strftime("%Y-%m-%d %H:%M")}',
                related_to='outpass',
                reference_id=outpass.id
            )
            db.session.add(notification)
            
        flash('Out pass approved successfully', 'success')
        
    elif decision == 'reject':
        if not comment:
            flash('Please provide a reason for rejection', 'danger')
            return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))
            
        outpass.status = 'rejected'
        outpass.approval_comment = comment
        
        # Notify the student
        notification = Notification(
            user_id=outpass.user_id,
            title='Out Pass Rejected',
            message=f'Your out pass request for {outpass.start_time.strftime("%Y-%m-%d %H:%M")} to {outpass.end_time.strftime("%Y-%m-%d %H:%M")} has been rejected with reason: {comment}',
            related_to='outpass',
            reference_id=outpass.id
        )
        db.session.add(notification)
        
        flash('Out pass rejected', 'warning')
        
    db.session.commit()
    return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))

@outpass_bp.route('/outpass/<int:outpass_id>/cancel', methods=['POST'])
@login_required
def cancel_outpass(outpass_id):
    if current_user.role != 'student':
        flash('Only students can cancel their out passes', 'danger')
        return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))
        
    outpass = OutPass.query.get_or_404(outpass_id)
    
    if outpass.user_id != current_user.id:
        flash('You can only cancel your own out passes', 'danger')
        return redirect(url_for('outpass.list_outpasses'))
        
    if outpass.status == 'approved' and outpass.start_time <= datetime.utcnow():
        flash('Cannot cancel an out pass that has already started', 'danger')
        return redirect(url_for('outpass.view_outpass', outpass_id=outpass_id))
        
    # Delete all notifications related to this outpass
    notifications = Notification.query.filter_by(related_to='outpass', reference_id=outpass.id).all()
    for notification in notifications:
        db.session.delete(notification)
        
    # Delete the outpass
    db.session.delete(outpass)
    db.session.commit()
    
    flash('Out pass cancelled successfully', 'info')
    return redirect(url_for('outpass.list_outpasses'))
