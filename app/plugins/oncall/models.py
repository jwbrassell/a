from app.extensions import db
from datetime import datetime, timedelta, timezone
import zoneinfo
from sqlalchemy import and_

class OnCallRotation(db.Model):
    __tablename__ = 'oncall_rotation'
    
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_current_oncall():
        """Get the current on-call person based on the time"""
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        current_time = datetime.now(central_tz)
        
        # Convert to UTC for database query
        current_time_utc = current_time.astimezone(timezone.utc)
        
        return OnCallRotation.query.filter(and_(
            OnCallRotation.start_time <= current_time_utc,
            OnCallRotation.end_time > current_time_utc
        )).first()

    @staticmethod
    def create_from_csv_row(row, year):
        """Create an on-call rotation entry from a CSV row"""
        week_num = int(row['week'])
        if week_num < 1 or week_num > 53:
            raise ValueError(f"Invalid week number: {week_num}")
        
        # Calculate the Friday 5 PM start time for this week
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        
        # Find the first day of the year
        jan_first = datetime(year, 1, 1)
        # Find the first Thursday (iso weekday 4)
        days_until_thursday = (4 - jan_first.isoweekday()) % 7
        first_thursday = jan_first + timedelta(days=days_until_thursday)
        # The week containing Jan 4 is the first week of the year
        first_week_monday = first_thursday - timedelta(days=3)
        
        # Calculate the Monday of our target week
        target_monday = first_week_monday + timedelta(weeks=week_num-1)
        # Calculate Friday 5 PM of our target week (start time)
        start_time = datetime.combine(
            (target_monday + timedelta(days=4)).date(),
            datetime.strptime("17:00", "%H:%M").time()
        ).replace(tzinfo=central_tz)
        
        # End time is the next Friday at 5 PM
        end_time = start_time + timedelta(days=7)

        # Validate that the dates make sense
        if start_time.year != year or end_time.year < year:
            raise ValueError(f"Week {week_num} is not valid for year {year}")

        # Convert to UTC for storage
        start_time_utc = start_time.astimezone(timezone.utc)
        end_time_utc = end_time.astimezone(timezone.utc)

        return OnCallRotation(
            week_number=week_num,
            year=year,
            person_name=row['name'].strip(),
            phone_number=row['phone'].strip(),
            start_time=start_time_utc,
            end_time=end_time_utc
        )

    @staticmethod
    def get_week_dates(year, week):
        """Get the start and end dates for a given week number"""
        jan_first = datetime(year, 1, 1)
        days_until_thursday = (4 - jan_first.isoweekday()) % 7
        first_thursday = jan_first + timedelta(days=days_until_thursday)
        first_week_monday = first_thursday - timedelta(days=3)
        target_monday = first_week_monday + timedelta(weeks=week-1)
        target_friday = target_monday + timedelta(days=4)
        
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime.combine(
            target_friday.date(),
            datetime.strptime("17:00", "%H:%M").time()
        ).replace(tzinfo=central_tz)
        
        end_time = start_time + timedelta(days=7)
        
        return start_time, end_time

    def to_dict(self):
        """Convert the rotation to a dictionary"""
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_central = self.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
        end_central = self.end_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
        
        return {
            'id': self.id,
            'week_number': self.week_number,
            'year': self.year,
            'person_name': self.person_name,
            'phone_number': self.phone_number,
            'start_time': start_central.isoformat(),
            'end_time': end_central.isoformat()
        }

    def __repr__(self):
        return f'<OnCallRotation {self.year}-W{self.week_number:02d} {self.person_name}>'
