from flask import render_template, request, jsonify, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import csv
from datetime import datetime, timezone
import zoneinfo
from . import bp
from .models import OnCallRotation, db

@bp.route('/')
@login_required
def index():
    return render_template('oncall/index.html')

@bp.route('/upload', methods=['POST'])
@login_required
def upload_oncall():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read CSV file
        csv_content = file.read().decode('utf-8-sig').splitlines()  # Handle BOM if present
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
        
        # Clear existing entries for the year
        OnCallRotation.query.filter_by(year=year).delete()
        
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
                
                rotation = OnCallRotation.create_from_csv_row({
                    'week': week,
                    'name': name,
                    'phone': phone
                }, year)
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
            'message': f'Successfully uploaded {row_count} on-call rotations for {year}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/events')
@login_required
def get_events():
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        
        if not start or not end:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Convert string dates to datetime with UTC timezone
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        # Query events in the date range
        events = OnCallRotation.query.filter(
            OnCallRotation.start_time < end_date,
            OnCallRotation.end_time > start_date
        ).all()
        
        # Format events for FullCalendar
        calendar_events = []
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        
        for event in events:
            # Convert UTC times to Central time for display
            start_central = event.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            end_central = event.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            
            calendar_events.append({
                'id': event.id,
                'title': f"{event.person_name}",
                'start': start_central.isoformat(),
                'end': end_central.isoformat(),
                'description': f"Phone: {event.phone_number}",
                'backgroundColor': '#007bff',
                'borderColor': '#0056b3',
                'textColor': '#ffffff',
                'allDay': False,
                'extendedProps': {
                    'week_number': event.week_number,
                    'phone': event.phone_number
                }
            })
        
        return jsonify(calendar_events)
    except Exception as e:
        current_app.logger.error(f"Error getting events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/current')
@login_required
def get_current_oncall():
    try:
        rotation = OnCallRotation.get_current_oncall()
        if rotation:
            central_tz = zoneinfo.ZoneInfo('America/Chicago')
            start_central = rotation.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            end_central = rotation.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
            
            return jsonify({
                'name': rotation.person_name,
                'phone': rotation.phone_number,
                'start': start_central.isoformat(),
                'end': end_central.isoformat()
            })
        return jsonify({'error': 'No on-call rotation found for current time'}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting current on-call: {str(e)}")
        return jsonify({'error': str(e)}), 500
