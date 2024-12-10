from flask import render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import csv
from datetime import datetime, timezone
import zoneinfo
import colorsys
from functools import wraps
from io import StringIO
from . import bp
from .models import OnCallRotation, Team, db
from sqlalchemy.exc import OperationalError
from app.utils.rbac import requires_roles

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('admin'):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    # Try to get teams, but handle case where table doesn't exist yet
    try:
        teams = Team.query.order_by(Team.name).all()
    except OperationalError:
        teams = []
        
    return render_template('oncall/index.html', 
                         is_admin=current_user.has_role('admin'),
                         teams=teams)

@bp.route('/api/teams', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_teams():
    if request.method == 'POST':
        try:
            data = request.get_json()
            name = data.get('name')
            color = data.get('color', 'primary')
            
            if not name:
                return jsonify({'error': 'Team name is required'}), 400
                
            # Check if team already exists
            existing_team = Team.query.filter_by(name=name).first()
            if existing_team:
                return jsonify({'error': 'Team already exists'}), 400
                
            team = Team(name=name, color=color)
            db.session.add(team)
            db.session.commit()
            
            return jsonify(team.to_dict())
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating team: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    # GET request - return list of teams
    try:
        teams = Team.query.order_by(Team.name).all()
        return jsonify([team.to_dict() for team in teams])
    except OperationalError:
        return jsonify([])

@bp.route('/api/teams/<int:team_id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def manage_team(team_id):
    team = Team.query.get_or_404(team_id)
    
    if request.method == 'DELETE':
        try:
            db.session.delete(team)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting team: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    # PUT request
    try:
        data = request.get_json()
        if 'name' in data:
            team.name = data['name']
        if 'color' in data:
            team.color = data['color']
            
        db.session.commit()
        return jsonify(team.to_dict())
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating team: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/upload', methods=['POST'])
@login_required
@admin_required
def upload_oncall():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Get team from form
        team_id = request.form.get('team')
        if not team_id:
            return jsonify({'error': 'Team is required'}), 400
            
        team = Team.query.get(team_id)
        if not team:
            return jsonify({'error': 'Invalid team selected'}), 400

        # Read CSV file
        csv_content = file.read().decode('utf-8-sig').splitlines()
        if not csv_content:
            return jsonify({'error': 'CSV file is empty'}), 400

        csv_reader = csv.DictReader(csv_content)
        required_fields = ['week', 'name', 'phone']
        
        # Validate CSV headers
        headers = csv_reader.fieldnames
        if not headers or not all(field in headers for field in required_fields):
            return jsonify({'error': f'CSV must contain columns: {", ".join(required_fields)}'}), 400
        
        # Get year from form data or use current year
        try:
            year = int(request.form.get('year', datetime.now().year))
            if year < 1900 or year > 9999:
                return jsonify({'error': 'Invalid year'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid year format'}), 400
        
        # Begin transaction
        db.session.begin_nested()
        
        # Clear existing entries for the team and year
        OnCallRotation.query.filter_by(team_id=team_id, year=year).delete()
        
        # Process each row
        row_count = 0
        for row in csv_reader:
            try:
                # Validate week number
                week = int(row['week'])
                if week < 1 or week > 53:
                    raise ValueError(f"Invalid week number: {week}")
                
                # Validate phone number format (basic check)
                phone = row['phone'].strip()
                if not phone:
                    raise ValueError("Phone number cannot be empty")
                
                # Validate name
                name = row['name'].strip()
                if not name:
                    raise ValueError("Name cannot be empty")
                
                rotation = OnCallRotation.create_from_csv_row(row, year, team_id)
                db.session.add(rotation)
                row_count += 1
                
            except (ValueError, KeyError) as e:
                db.session.rollback()
                return jsonify({'error': f'Error in CSV row {row_count + 1}: {str(e)}'}), 400
        
        if row_count == 0:
            return jsonify({'error': 'No valid rows found in CSV'}), 400
        
        # Commit transaction
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully uploaded {row_count} on-call rotations for {team.name} in {year}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/events')
@login_required
def get_events():
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        team_id = request.args.get('team')  # Optional team filter
        
        if not start or not end:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Convert string dates to datetime with UTC timezone
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        # Query events in the date range
        query = OnCallRotation.query.filter(
            OnCallRotation.start_time < end_date,
            OnCallRotation.end_time > start_date
        )

        # Apply team filter if provided
        if team_id:
            query = query.filter_by(team_id=team_id)

        events = query.all()
        
        # Format events for FullCalendar
        calendar_events = []
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        
        for event in events:
            # Convert UTC times to Central time for display
            start_central = event.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            end_central = event.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            
            calendar_events.append({
                'id': event.id,
                'title': event.person_name,
                'start': start_central.isoformat(),
                'end': end_central.isoformat(),
                'description': f"Phone: {event.phone_number}",
                'classNames': [f'bg-{event.team.color}'],
                'textColor': '#ffffff',
                'allDay': True,  # Show as all-day events for better visibility
                'display': 'block',  # Make events take up full width
                'extendedProps': {
                    'week_number': event.week_number,
                    'phone': event.phone_number,
                    'team': event.team.name,
                    'team_id': event.team_id
                }
            })
        
        return jsonify(calendar_events)
    except OperationalError:
        # If team table doesn't exist yet, return empty list
        return jsonify([])
    except Exception as e:
        current_app.logger.error(f"Error getting events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/current')
@login_required
def get_current_oncall():
    try:
        team_id = request.args.get('team')  # Optional team filter
        rotation = OnCallRotation.get_current_oncall(team_id)
        if rotation:
            central_tz = zoneinfo.ZoneInfo('America/Chicago')
            start_central = rotation.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            end_central = rotation.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            
            return jsonify({
                'name': rotation.person_name,
                'phone': rotation.phone_number,
                'team': rotation.team.name,
                'color': rotation.team.color,
                'start': start_central.isoformat(),
                'end': end_central.isoformat()
            })
        return jsonify({'error': 'No on-call rotation found for current time'}), 404
    except OperationalError:
        return jsonify({'error': 'No on-call rotation found for current time'}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting current on-call: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/export/<int:team_id>/<int:year>')
@login_required
def export_schedule(team_id, year):
    try:
        format = request.args.get('format', 'json')
        if format not in ['json', 'csv']:
            return jsonify({'error': 'Invalid export format'}), 400

        # Verify team exists
        team = Team.query.get_or_404(team_id)
        
        data = OnCallRotation.export_team_schedule(team_id, year, format)
        
        if format == 'json':
            return jsonify(json.loads(data))
        else:  # CSV
            output = StringIO(data)
            filename = f"oncall_schedule_{team.name}_{year}.csv"
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        current_app.logger.error(f"Error exporting schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500
