"""Routes for on-call rotation management."""

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import csv
from datetime import datetime, timezone
import zoneinfo
from functools import wraps
from . import bp
from .models import OnCallRotation, Team, CompanyHoliday, db
from sqlalchemy.exc import OperationalError
import io
import traceback

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not any(role.name.lower() == 'administrator' for role in current_user.roles):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    """Render the main on-call schedule view."""
    try:
        teams = Team.query.order_by(Team.name).all()
    except OperationalError:
        teams = []
        
    # Debug information about user roles
    user_roles = [role.name for role in current_user.roles]
    current_app.logger.info(f"User {current_user.username} has roles: {user_roles}")
    
    return render_template('oncall/index.html', 
                         is_admin=any(role.name.lower() == 'administrator' for role in current_user.roles),
                         teams=teams,
                         now=datetime.now())

@bp.route('/api/teams', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_teams():
    """API endpoint for managing teams."""
    if request.method == 'POST':
        try:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
                
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

@bp.route('/api/teams/<int:team_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@admin_required
def manage_team(team_id):
    """API endpoint for managing a specific team."""
    team = Team.query.get_or_404(team_id)
    
    if request.method == 'GET':
        return jsonify(team.to_dict())
    
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
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
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
    """API endpoint for uploading on-call schedules via CSV."""
    current_app.logger.info("Starting file upload process")
    
    if 'file' not in request.files:
        current_app.logger.error("No file in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        current_app.logger.error("Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        current_app.logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Get team from form
        team_id = request.form.get('team')
        if not team_id:
            current_app.logger.error("No team provided")
            return jsonify({'error': 'Team is required'}), 400
            
        team = Team.query.get(team_id)
        if not team:
            current_app.logger.error(f"Invalid team ID: {team_id}")
            return jsonify({'error': 'Invalid team selected'}), 400

        # Get year from form data or use current year
        try:
            year = int(request.form.get('year', datetime.now().year))
            if year < 1900 or year > 9999:
                current_app.logger.error(f"Invalid year: {year}")
                return jsonify({'error': 'Invalid year'}), 400
        except ValueError as e:
            current_app.logger.error(f"Year parsing error: {str(e)}")
            return jsonify({'error': 'Invalid year format'}), 400

        # Check if auto-generate is requested
        auto_generate = request.form.get('auto_generate') == 'true'

        # Read and validate CSV file
        try:
            # Read file content into memory
            file_content = file.read()
            
            # Try different encodings
            encodings = ['utf-8-sig', 'utf-8', 'ascii']
            csv_content = None
            
            for encoding in encodings:
                try:
                    csv_content = file_content.decode(encoding)
                    current_app.logger.info(f"Successfully decoded file with {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if csv_content is None:
                current_app.logger.error("Failed to decode file with any encoding")
                return jsonify({'error': 'Unable to read CSV file. Please ensure it is properly encoded.'}), 400

            if not csv_content.strip():
                current_app.logger.error("Empty CSV file")
                return jsonify({'error': 'CSV file is empty'}), 400

            # Parse CSV content
            rows = []
            reader = csv.DictReader(io.StringIO(csv_content))
            
            if auto_generate:
                required_fields = ['name', 'phone']
            else:
                required_fields = ['week', 'name', 'phone']
            
            # Validate CSV headers
            if not all(field in reader.fieldnames for field in required_fields):
                current_app.logger.error(f"Missing required fields. Found: {reader.fieldnames}")
                return jsonify({'error': f'CSV must contain columns: {", ".join(required_fields)}'}), 400

            # Collect all rows first for validation
            for row_num, row in enumerate(reader, start=1):
                # Basic validation
                if not all(row.get(field, '').strip() for field in required_fields):
                    current_app.logger.error(f"Missing values in row {row_num}: {row}")
                    return jsonify({'error': f'All required fields must have values (row {row_num})'}), 400
                
                if not auto_generate:
                    try:
                        week = int(row['week'])
                        if week < 1 or week > 53:
                            current_app.logger.error(f"Invalid week number in row {row_num}: {week}")
                            return jsonify({'error': f'Invalid week number: {week} (row {row_num})'}), 400
                    except ValueError:
                        current_app.logger.error(f"Invalid week format in row {row_num}: {row['week']}")
                        return jsonify({'error': f'Invalid week number format: {row["week"]} (row {row_num})'}), 400
                rows.append(row)

            if not rows:
                current_app.logger.error("No valid rows found in CSV")
                return jsonify({'error': 'No valid rows found in CSV'}), 400

            current_app.logger.info(f"Found {len(rows)} valid rows in CSV")

            # Begin transaction
            db.session.begin_nested()

            if auto_generate:
                # Extract names and phones for schedule generation
                names_and_phones = [(row['name'].strip(), row['phone'].strip()) for row in rows]
                
                # Delete existing rotations for this team and year
                OnCallRotation.query.filter_by(team_id=team_id, year=year).delete()
                
                # Generate and save new schedule
                schedule = OnCallRotation.generate_schedule(team_id, year, names_and_phones)
                for rotation in schedule:
                    db.session.add(rotation)
                
                message = f'Successfully generated schedule with {len(schedule)} rotations for {team.name} in {year}'
            else:
                # Instead of deleting, update existing entries or create new ones
                for row in rows:
                    try:
                        week_num = int(row['week'])
                        # Try to find existing rotation for this week
                        rotation = OnCallRotation.query.filter_by(
                            team_id=team_id,
                            year=year,
                            week_number=week_num
                        ).first()
                        
                        if rotation:
                            # Update existing rotation
                            rotation.person_name = row['name'].strip()
                            rotation.phone_number = row['phone'].strip()
                            # Recalculate dates in case the algorithm has been updated
                            new_rotation = OnCallRotation.create_from_csv_row(row, year, team_id)
                            rotation.start_time = new_rotation.start_time
                            rotation.end_time = new_rotation.end_time
                            current_app.logger.info(f"Updated rotation for week {week_num}")
                        else:
                            # Create new rotation
                            rotation = OnCallRotation.create_from_csv_row(row, year, team_id)
                            db.session.add(rotation)
                            current_app.logger.info(f"Created new rotation for week {week_num}")
                    except Exception as e:
                        current_app.logger.error(f"Error processing row: {row}")
                        current_app.logger.error(traceback.format_exc())
                        raise ValueError(f"Error processing week {row['week']}: {str(e)}")
                
                message = f'Successfully uploaded {len(rows)} on-call rotations for {team.name} in {year}'

            # Commit transaction
            db.session.commit()
            
            current_app.logger.info(message)
            return jsonify({'message': message})
            
        except Exception as e:
            current_app.logger.error(f"Error processing CSV content: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in upload process: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@bp.route('/api/holidays/upload', methods=['POST'])
@login_required
@admin_required
def upload_holidays():
    """API endpoint for uploading company holidays via CSV."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read file content
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        # Validate headers
        required_fields = ['name', 'date']
        if not all(field in reader.fieldnames for field in required_fields):
            return jsonify({'error': f'CSV must contain columns: {", ".join(required_fields)}'}), 400
        
        # Begin transaction
        db.session.begin_nested()
        
        # Process each row
        holidays = []
        for row in reader:
            try:
                holiday = CompanyHoliday.create_from_csv_row(row)
                holidays.append(holiday)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        if not holidays:
            return jsonify({'error': 'No valid holidays found in CSV'}), 400
        
        # Get the year of the first holiday
        year = holidays[0].date.year
        
        # Delete existing holidays for this year
        CompanyHoliday.query.filter(
            db.extract('year', CompanyHoliday.date) == year
        ).delete()
        
        # Add new holidays
        for holiday in holidays:
            db.session.add(holiday)
        
        db.session.commit()
        return jsonify({
            'message': f'Successfully uploaded {len(holidays)} holidays for {year}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading holidays: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/holidays')
@login_required
def get_holidays():
    """API endpoint for retrieving holidays."""
    try:
        year = request.args.get('year', type=int)
        if not year:
            return jsonify({'error': 'Year parameter is required'}), 400
            
        holidays = CompanyHoliday.query.filter(
            db.extract('year', CompanyHoliday.date) == year
        ).order_by(CompanyHoliday.date).all()
        
        return jsonify([{
            'id': h.id,
            'name': h.name,
            'date': h.date.isoformat()
        } for h in holidays])
        
    except Exception as e:
        current_app.logger.error(f"Error getting holidays: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/events')
@login_required
def get_events():
    """API endpoint for retrieving calendar events."""
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
            query = query.filter_by(team_id=int(team_id))

        events = query.all()
        
        # Get holidays in the date range
        holidays = CompanyHoliday.query.filter(
            CompanyHoliday.date >= start_date.date(),
            CompanyHoliday.date <= end_date.date()
        ).all()
        
        # Format events for FullCalendar
        calendar_events = []
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        
        # Add on-call rotations
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
            
        # Add holidays
        for holiday in holidays:
            calendar_events.append({
                'id': f'holiday-{holiday.id}',
                'title': f'🎉 {holiday.name}',
                'start': holiday.date.isoformat(),
                'allDay': True,
                'display': 'background',
                'backgroundColor': '#ff9f89',
                'classNames': ['holiday-event']
            })
        
        return jsonify(calendar_events)
    except OperationalError:
        # If team table doesn't exist yet, return empty list
        return jsonify([])
    except Exception as e:
        current_app.logger.error(f"Error getting events: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@bp.route('/api/current')
@login_required
def get_current_oncall():
    """API endpoint for getting the current on-call person."""
    try:
        team_id = request.args.get('team')
        if team_id:
            try:
                team_id = int(team_id)
                # Verify team exists
                team = Team.query.get(team_id)
                if not team:
                    return jsonify({
                        'name': 'No one currently on call',
                        'phone': '-',
                        'message': 'Team not found'
                    }), 200
            except ValueError:
                return jsonify({
                    'name': 'No one currently on call',
                    'phone': '-',
                    'message': 'Invalid team ID'
                }), 200

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
            }), 200
        
        # Return empty state with 200 status when no one is on call
        message = 'No one currently on call'
        if team_id:
            team = Team.query.get(team_id)
            if team:
                message += f' for {team.name}'
        return jsonify({
            'name': message,
            'phone': '-'
        }), 200

    except OperationalError:
        return jsonify({
            'name': 'No one currently on call',
            'phone': '-',
            'message': 'Database error occurred'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting current on-call: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'name': 'No one currently on call',
            'phone': '-',
            'message': str(e)
        }), 200
