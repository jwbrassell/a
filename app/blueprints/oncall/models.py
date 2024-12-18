"""Models for on-call rotation management."""

from app.extensions import db
from datetime import datetime, timedelta, timezone
import zoneinfo
from sqlalchemy import and_
import csv
import json
from io import StringIO
import random

class CompanyHoliday(db.Model):
    """Model for company holidays."""
    
    __tablename__ = 'company_holiday'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    @staticmethod
    def create_from_csv_row(row):
        """Create a holiday entry from a CSV row."""
        try:
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
            holiday_date = None
            
            for fmt in date_formats:
                try:
                    holiday_date = datetime.strptime(row['date'].strip(), fmt).date()
                    break
                except ValueError:
                    continue
                    
            if not holiday_date:
                raise ValueError(f"Invalid date format: {row['date']}")
                
            return CompanyHoliday(
                name=row['name'].strip(),
                date=holiday_date
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")

class Team(db.Model):
    """Team model for organizing on-call rotations."""
    
    __tablename__ = 'oncall_team'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), nullable=False, default='primary')  # Bootstrap color class
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    rotations = db.relationship('OnCallRotation', backref='team', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert team to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class OnCallRotation(db.Model):
    """Model for individual on-call rotation assignments."""
    
    __tablename__ = 'oncall_rotation'
    
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('oncall_team.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_current_oncall(team_id=None):
        """Get the current on-call person based on the time and optionally filtered by team."""
        # Get current time in Central timezone
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        current_time = datetime.now(central_tz)
        
        # Convert to UTC for database query
        current_time_utc = current_time.astimezone(timezone.utc)
        
        # Build query for current time
        query = OnCallRotation.query.filter(
            OnCallRotation.start_time <= current_time_utc,
            OnCallRotation.end_time > current_time_utc
        )

        # Add team filter if provided
        if team_id:
            query = query.filter_by(team_id=team_id)
            
        return query.first()

    @staticmethod
    def create_from_csv_row(row, year, team_id):
        """Create an on-call rotation entry from a CSV row."""
        week_num = int(row['week'])
        if week_num < 1 or week_num > 53:  # Fixed: using week_num consistently
            raise ValueError(f"Invalid week number: {week_num}")
        
        # Calculate the Friday 5 PM start time for this week
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        
        # Get the date of the first day of the year
        jan_first = datetime(year, 1, 1)
        
        # Calculate the start of week 1
        # Week 1 is the week containing January 1st
        days_to_monday = (jan_first.weekday() - 0) % 7  # Days until previous Monday
        first_monday = jan_first - timedelta(days=days_to_monday)
        
        # Calculate target week's Monday
        target_monday = first_monday + timedelta(weeks=week_num-1)
        
        # Calculate Friday 5 PM of target week (start time)
        start_time = datetime.combine(
            (target_monday + timedelta(days=4)).date(),  # Friday
            datetime.strptime("17:00", "%H:%M").time()
        ).replace(tzinfo=central_tz)
        
        # End time is the next Friday at 5 PM
        end_time = start_time + timedelta(days=7)

        # Convert to UTC for storage
        start_time_utc = start_time.astimezone(timezone.utc)
        end_time_utc = end_time.astimezone(timezone.utc)

        return OnCallRotation(
            week_number=week_num,
            year=year,
            person_name=row['name'].strip(),
            phone_number=row['phone'].strip(),
            team_id=team_id,
            start_time=start_time_utc,
            end_time=end_time_utc
        )

    @staticmethod
    def generate_schedule(team_id, year, names_and_phones):
        """Generate a full year schedule based on provided names."""
        # Get all holidays for the year
        holidays = CompanyHoliday.query.filter(
            db.extract('year', CompanyHoliday.date) == year
        ).all()
        holiday_dates = {h.date for h in holidays}
        
        # Get the total number of weeks in the year
        jan_first = datetime(year, 1, 1)
        dec_31 = datetime(year, 12, 31)
        total_weeks = int((dec_31 - jan_first).days / 7) + 1
        
        # Create a list of all weeks with their holiday count
        weeks = []
        for week_num in range(1, total_weeks + 1):
            start_time, end_time = OnCallRotation.get_week_dates(year, week_num)
            
            # Count holidays in this week
            holiday_count = 0
            current = start_time
            while current < end_time:
                if current.date() in holiday_dates:
                    holiday_count += 1
                current += timedelta(days=1)
            
            weeks.append({
                'week_number': week_num,
                'holiday_count': holiday_count
            })
        
        # Sort weeks by holiday count (descending) to assign high-holiday weeks first
        weeks.sort(key=lambda x: x['holiday_count'], reverse=True)
        
        # Track assignments per person for fair distribution
        assignments = {name: 0 for name, _ in names_and_phones}
        
        # Create schedule
        schedule = []
        for week in weeks:
            # Find person with fewest assignments
            eligible_persons = sorted(assignments.items(), key=lambda x: x[1])
            person_name = eligible_persons[0][0]
            
            # Get phone number for selected person
            phone_number = next(phone for name, phone in names_and_phones if name == person_name)
            
            # Create rotation
            start_time, end_time = OnCallRotation.get_week_dates(year, week['week_number'])
            rotation = OnCallRotation(
                week_number=week['week_number'],
                year=year,
                person_name=person_name,
                phone_number=phone_number,
                team_id=team_id,
                start_time=start_time.astimezone(timezone.utc),
                end_time=end_time.astimezone(timezone.utc)
            )
            
            schedule.append(rotation)
            assignments[person_name] += 1
        
        # Sort schedule by week number
        schedule.sort(key=lambda x: x.week_number)
        return schedule

    @staticmethod
    def get_week_number(date):
        """Get the ISO week number for a given date."""
        return date.isocalendar()[1]

    @staticmethod
    def get_week_dates(year, week):
        """Get the start and end dates for a given week number."""
        jan_first = datetime(year, 1, 1)
        days_to_monday = (jan_first.weekday() - 0) % 7
        first_monday = jan_first - timedelta(days=days_to_monday)
        target_monday = first_monday + timedelta(weeks=week-1)
        target_friday = target_monday + timedelta(days=4)
        
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime.combine(
            target_friday.date(),
            datetime.strptime("17:00", "%H:%M").time()
        ).replace(tzinfo=central_tz)
        
        end_time = start_time + timedelta(days=7)
        
        return start_time, end_time

    def to_dict(self):
        """Convert the rotation to a dictionary."""
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_central = self.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
        end_central = self.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
        
        return {
            'id': self.id,
            'week_number': self.week_number,
            'year': self.year,
            'person_name': self.person_name,
            'phone_number': self.phone_number,
            'team': self.team.to_dict(),
            'start_time': start_central.isoformat(),
            'end_time': end_central.isoformat()
        }

    @staticmethod
    def export_team_schedule(team_id, year, format='json'):
        """Export a team's schedule in the specified format."""
        rotations = OnCallRotation.query.filter_by(
            team_id=team_id,
            year=year
        ).order_by(OnCallRotation.week_number).all()

        if format == 'json':
            return json.dumps([rotation.to_dict() for rotation in rotations], indent=2)
        elif format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Week', 'Name', 'Phone', 'Start Time', 'End Time'])
            
            for rotation in rotations:
                central_tz = zoneinfo.ZoneInfo('America/Chicago')
                start_central = rotation.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
                end_central = rotation.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
                
                writer.writerow([
                    rotation.week_number,
                    rotation.person_name,
                    rotation.phone_number,
                    start_central.isoformat(),
                    end_central.isoformat()
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def __repr__(self):
        return f'<OnCallRotation {self.year}-W{self.week_number:02d} {self.team.name} - {self.person_name}>'
