import os
import csv
import io
import shutil
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, make_response, Response, redirect, url_for
from flask_wtf.csrf import validate_csrf, ValidationError
from flask_login import current_user, login_required
from app.utils.enhanced_rbac import requires_permission
from werkzeug.utils import secure_filename
from app.extensions import db
from .models import BugReport, BugReportScreenshot
from datetime import datetime

bp = Blueprint('bug_reports', __name__, 
              url_prefix='/bug_reports',
              template_folder='templates')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@bp.route('/reports', methods=['GET', 'POST'])  # Will become /bug_reports/reports with prefix
@login_required
@requires_permission('bug_reports')
def submit_bug_report():
    if request.method == 'GET':
        return redirect(url_for('bug_reports.view_reports'))
    current_app.logger.info(f"Received POST request to /reports")
    current_app.logger.info(f"Request URL: {request.url}")
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Request headers: {dict(request.headers)}")
    try:
        # Validate CSRF token
        try:
            csrf_token = request.headers.get('X-CSRFToken')
            if not csrf_token:
                return jsonify({'status': 'error', 'message': 'CSRF token missing'}), 400
            validate_csrf(csrf_token)
        except ValidationError as e:
            current_app.logger.error(f"CSRF validation failed: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 400

        current_app.logger.debug(f"Received bug report submission from user {current_user.id}")
        current_app.logger.debug(f"Form data: {request.form}")
        current_app.logger.debug(f"Files: {request.files}")
        
        # Validate required fields
        if 'description' not in request.form:
            return jsonify({'status': 'error', 'message': 'Description is required'}), 400
        if 'occurrence_type' not in request.form:
            return jsonify({'status': 'error', 'message': 'Occurrence type is required'}), 400
        if 'route' not in request.form:
            return jsonify({'status': 'error', 'message': 'Route is required'}), 400
            
        data = request.form
        
        # Create bug report
        bug_report = BugReport(
            user_id=current_user.id,
            route=data['route'],
            description=data['description'],
            occurrence_type=data['occurrence_type'],
            user_roles=','.join(current_user.get_roles())
        )
        db.session.add(bug_report)
        db.session.flush()  # Get the ID without committing
        
        # Handle screenshots
        screenshots = request.files.getlist('screenshots')
        upload_path = os.path.join(current_app.root_path, 'instance', 'uploads', 'bug_reports', str(bug_report.id))
        os.makedirs(upload_path, exist_ok=True)
        
        for screenshot in screenshots:
            if screenshot and allowed_file(screenshot.filename):
                filename = secure_filename(screenshot.filename)
                screenshot.save(os.path.join(upload_path, filename))
                
                screenshot_record = BugReportScreenshot(
                    bug_report_id=bug_report.id,
                    filename=filename
                )
                db.session.add(screenshot_record)
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Bug report submitted successfully',
            'report_id': bug_report.id,
            'redirect_url': f'/bug_reports/ticket/{bug_report.id}'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error submitting bug report: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/')
@login_required
@requires_permission('bug_reports')
def view_reports():
    open_reports = BugReport.query.filter(BugReport.status != 'solved').order_by(BugReport.created_at.desc()).all()
    closed_reports = BugReport.query.filter(BugReport.status == 'solved').order_by(BugReport.created_at.desc()).all()
    return render_template('list.html', open_reports=open_reports, closed_reports=closed_reports, title='Bug Reports')

@bp.route('/reports/<int:report_id>', methods=['PUT'])  # Will become /bug_reports/reports/<id> with prefix
@login_required
@requires_permission('bug_reports')
def update_report(report_id):
    try:
        # Validate CSRF token
        try:
            csrf_token = request.headers.get('X-CSRFToken')
            if not csrf_token:
                raise ValidationError('CSRF token missing')
            validate_csrf(csrf_token)
        except ValidationError as e:
            current_app.logger.error(f"CSRF validation failed: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 400

        report = BugReport.query.get_or_404(report_id)
        data = request.json
    
        if 'status' in data:
            report.status = data['status']
        if 'merged_with' in data:
            report.merged_with = data['merged_with']
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Report updated successfully',
            'report_id': report_id
        })
    except Exception as e:
        current_app.logger.error(f"Error updating bug report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/ticket/<int:report_id>')
@login_required
@requires_permission('bug_reports')
def view_ticket(report_id):
    report = BugReport.query.get_or_404(report_id)
    all_reports = BugReport.query.order_by(BugReport.created_at.desc()).all()
    return render_template('ticket.html', report=report, all_reports=all_reports)

@bp.route('/admin')
@login_required
@requires_permission('bug_reports_admin')
def admin_dashboard():
    # Calculate statistics
    total_reports = BugReport.query.count()
    open_reports = BugReport.query.filter(BugReport.status == 'open').count()
    solved_reports = BugReport.query.filter(BugReport.status == 'solved').count()
    
    # Calculate average resolution time for solved reports
    solved_reports_data = BugReport.query.filter(
        BugReport.status == 'solved',
        BugReport.updated_at.isnot(None)
    ).all()
    
    if solved_reports_data:
        total_resolution_time = sum(
            (report.updated_at - report.created_at).total_seconds() / 3600
            for report in solved_reports_data
        )
        avg_resolution_time = f"{total_resolution_time / len(solved_reports_data):.1f} hours"
    else:
        avg_resolution_time = "N/A"

    stats = {
        'total': total_reports,
        'open': open_reports,
        'solved': solved_reports,
        'avg_resolution_time': avg_resolution_time
    }

    return render_template('admin_dashboard.html', stats=stats)

@bp.route('/admin/data')
@login_required
@requires_permission('bug_reports_admin')
def admin_data():
    try:
        current_app.logger.info("=== Starting admin_data request ===")
        current_app.logger.info(f"Request args: {request.args}")
        
        # Get DataTables parameters
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=25)
        search_value = request.args.get('search[value]', type=str)
        
        current_app.logger.info(f"DataTables params - Draw: {draw}, Start: {start}, Length: {length}")
        
        # Base query
        query = BugReport.query
        current_app.logger.info("Base query created")
        
        # Apply filters
        # Get all status parameters (status[0], status[1], etc.)
        status_filters = []
        for key in request.args:
            if key.startswith('status['):
                status_filters.append(request.args[key])
        
        current_app.logger.info(f"Status filter values: {status_filters}")
        if status_filters:
            query = query.filter(BugReport.status.in_(status_filters))
            current_app.logger.info(f"Applied status filter with values: {status_filters}")
        
        type_filter = request.args.get('type')
        current_app.logger.info(f"Type filter value: {type_filter}")
        if type_filter and type_filter != 'all':
            query = query.filter(BugReport.occurrence_type == type_filter)
        
        route_filter = request.args.get('route')
        current_app.logger.info(f"Route filter value: {route_filter}")
        if route_filter:
            query = query.filter(BugReport.route.ilike(f'%{route_filter}%'))
        
        # Apply search
        if search_value:
            current_app.logger.info(f"Applying search value: {search_value}")
            query = query.filter(
                db.or_(
                    BugReport.route.ilike(f'%{search_value}%'),
                    BugReport.description.ilike(f'%{search_value}%'),
                    BugReport.status.ilike(f'%{search_value}%'),
                    BugReport.occurrence_type.ilike(f'%{search_value}%')
                )
            )
        
        # Log the SQL query being generated
        current_app.logger.info(f"Generated SQL: {query}")
        
        # Get total and filtered record counts
        total_records = BugReport.query.count()
        total_filtered = query.count()
        
        current_app.logger.info(f"Total records: {total_records}, Filtered records: {total_filtered}")
        
        # Apply pagination and ordering
        query = query.order_by(BugReport.created_at.desc())
        query = query.offset(start).limit(length)
        
        # Format data for DataTables
        data = []
        reports = query.all()
        current_app.logger.info(f"Retrieved {len(reports)} reports")
        
        for report in reports:
            data.append({
                'id': report.id,
                'user': report.user.username,
                'route': report.route,
                'type': report.occurrence_type,
                'status': report.status,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': report.updated_at.strftime('%Y-%m-%d %H:%M') if report.updated_at else '-'
            })
        
        response_data = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_filtered,
            'data': data
        }
        
        current_app.logger.info("=== Completed admin_data request successfully ===")
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in admin_data: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return jsonify({
            'error': str(e),
            'draw': request.args.get('draw', type=int),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        }), 500

@bp.route('/export')
@login_required
@requires_permission('bug_reports_admin')
def export_reports():
    # Create CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['ID', 'Reported By', 'Route', 'Type', 'Status', 'Description', 
                    'User Roles', 'Created At', 'Updated At'])
    
    # Write data
    reports = BugReport.query.order_by(BugReport.created_at.desc()).all()
    for report in reports:
        writer.writerow([
            report.id,
            report.user.username,
            report.route,
            report.occurrence_type,
            report.status,
            report.description,
            report.user_roles,
            report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            report.updated_at.strftime('%Y-%m-%d %H:%M:%S') if report.updated_at else ''
        ])
    
    # Create response
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bug_reports.csv'}
    )

@bp.route('/reports/<int:report_id>', methods=['DELETE'])
@login_required
@requires_permission('bug_reports_admin')
def delete_report(report_id):
    try:
        report = BugReport.query.get_or_404(report_id)
        
        # Delete associated screenshots
        upload_path = os.path.join(current_app.root_path, 'instance', 'uploads', 'bug_reports', str(report.id))
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path)
        
        # Delete from database
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Report deleted successfully'
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting bug report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/screenshot/<int:report_id>/<path:filename>')
@login_required
@requires_permission('bug_reports')
def get_screenshot(report_id, filename):
    upload_path = os.path.join(current_app.root_path, 'instance', 'uploads', 'bug_reports', str(report_id))
    return send_from_directory(upload_path, filename)
