"""Utility for handling bulk user operations."""

import csv
from io import StringIO
from typing import Dict, List, Any, Tuple
from app.models import User, Role
from app import db
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime
from app.utils.email_service import send_notification_email

logger = logging.getLogger(__name__)

class BulkUserOperations:
    """Handle bulk user operations like CSV import/export."""
    
    CSV_HEADERS = ['username', 'email', 'name', 'roles', 'is_active']
    
    @staticmethod
    def generate_temp_password() -> str:
        """Generate a temporary password for new users."""
        from secrets import token_urlsafe
        return token_urlsafe(12)
    
    @classmethod
    def export_users_to_csv(cls) -> str:
        """Export all users to CSV format."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=cls.CSV_HEADERS)
        writer.writeheader()
        
        users = User.query.all()
        for user in users:
            writer.writerow({
                'username': user.username,
                'email': user.email,
                'name': user.name or '',
                'roles': ','.join(role.name for role in user.roles),
                'is_active': str(user.is_active).lower()
            })
        
        return output.getvalue()
    
    @classmethod
    def import_users_from_csv(cls, csv_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Import users from CSV content.
        Returns tuple of (successful_imports, failed_imports)
        """
        successful_imports = []
        failed_imports = []
        
        try:
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            if not all(header in reader.fieldnames for header in cls.CSV_HEADERS):
                raise ValueError("CSV file missing required headers")
            
            for row in reader:
                try:
                    # Check if user already exists
                    existing_user = User.query.filter_by(username=row['username']).first()
                    if existing_user:
                        failed_imports.append({
                            'row': row,
                            'error': 'Username already exists'
                        })
                        continue
                    
                    # Generate temporary password
                    temp_password = cls.generate_temp_password()
                    
                    # Create new user
                    user = User(
                        username=row['username'],
                        email=row['email'],
                        name=row.get('name', ''),
                        is_active=str(row.get('is_active', 'true')).lower() == 'true',
                        password_hash=generate_password_hash(temp_password)
                    )
                    
                    # Handle role assignment
                    if row.get('roles'):
                        role_names = [r.strip() for r in row['roles'].split(',')]
                        roles = Role.query.filter(Role.name.in_(role_names)).all()
                        user.roles = roles
                    
                    db.session.add(user)
                    
                    # Send welcome email with temporary password
                    cls._send_welcome_email(user, temp_password)
                    
                    successful_imports.append({
                        'username': user.username,
                        'email': user.email,
                        'temp_password': temp_password
                    })
                    
                except Exception as e:
                    logger.error(f"Error importing user {row.get('username')}: {e}")
                    failed_imports.append({
                        'row': row,
                        'error': str(e)
                    })
                    db.session.rollback()
                    continue
            
            db.session.commit()
            return successful_imports, failed_imports
            
        except Exception as e:
            logger.error(f"Error processing CSV import: {e}")
            raise
    
    @staticmethod
    def _send_welcome_email(user: User, temp_password: str):
        """Send welcome email to newly imported user."""
        subject = "Welcome to the System"
        body = f"""
Hello {user.name or user.username},

Your account has been created with the following details:

Username: {user.username}
Temporary Password: {temp_password}

Please change your password upon first login.

Best regards,
System Admin
"""
        try:
            send_notification_email(subject, body, [user.email])
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {e}")
    
    @classmethod
    def batch_assign_roles(cls, user_ids: List[int], role_ids: List[int], 
                         operation: str = 'add') -> Dict[str, Any]:
        """
        Batch assign or remove roles for multiple users.
        operation: 'add' or 'remove'
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(user_ids)
        }
        
        try:
            users = User.query.filter(User.id.in_(user_ids)).all()
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            
            for user in users:
                try:
                    if operation == 'add':
                        for role in roles:
                            if role not in user.roles:
                                user.roles.append(role)
                    else:  # remove
                        for role in roles:
                            if role in user.roles:
                                user.roles.remove(role)
                    
                    user.updated_at = datetime.utcnow()
                    
                    results['successful'].append({
                        'username': user.username,
                        'email': user.email,
                        'roles': [r.name for r in user.roles]
                    })
                    
                except Exception as e:
                    results['failed'].append({
                        'username': user.username,
                        'error': str(e)
                    })
            
            db.session.commit()
            return results
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in batch role assignment: {e}")
            raise
    
    @staticmethod
    def generate_import_template() -> str:
        """Generate a CSV template for user import."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(BulkUserOperations.CSV_HEADERS)
        writer.writerow([
            'john.doe',
            'john.doe@example.com',
            'John Doe',
            'Basic User,Read Only',
            'true'
        ])
        return output.getvalue()
