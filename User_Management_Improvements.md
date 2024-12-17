# User Management Improvements Implementation

## 1. Bulk User Operations

### Current Status
- Individual user creation/editing
- Basic role assignment
- Avatar handling
- Activity tracking

### Improvements

#### A. CSV Import/Export Functionality

1. CSV Template Structure
```csv
username,email,full_name,roles,is_active
john.doe,john.doe@example.com,John Doe,"Basic User,Read Only",true
jane.smith,jane.smith@example.com,Jane Smith,Basic User,true
```

2. Implementation
```python
def process_user_csv(file_path, operation='import'):
    """Process user CSV for import/export operations."""
    if operation == 'import':
        results = {
            'success': [],
            'failed': [],
            'total': 0
        }
        
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Create user with basic info
                    user = User(
                        username=row['username'],
                        email=row['email'],
                        full_name=row.get('full_name', ''),
                        is_active=str(row.get('is_active', 'true')).lower() == 'true',
                        created_by='system_import'
                    )
                    
                    # Set default password (to be changed on first login)
                    temp_password = generate_temp_password()
                    user.set_password(temp_password)
                    
                    # Assign roles
                    if row.get('roles'):
                        role_names = [r.strip() for r in row['roles'].split(',')]
                        roles = Role.query.filter(Role.name.in_(role_names)).all()
                        user.roles = roles
                    
                    db.session.add(user)
                    results['success'].append({
                        'username': user.username,
                        'temp_password': temp_password
                    })
                    
                except Exception as e:
                    results['failed'].append({
                        'username': row.get('username'),
                        'error': str(e)
                    })
                
                results['total'] += 1
        
        db.session.commit()
        return results
    
    elif operation == 'export':
        users = User.query.all()
        output = []
        for user in users:
            output.append({
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'roles': ','.join(r.name for r in user.roles),
                'is_active': user.is_active
            })
        return output
```

#### B. Batch Role Assignment

1. Implementation
```python
def batch_assign_roles(user_ids, role_ids, operation='add'):
    """Batch assign or remove roles for multiple users."""
    results = {
        'success': [],
        'failed': [],
        'total': len(user_ids)
    }
    
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
            
            results['success'].append(user.username)
            
            # Send notification
            send_role_update_notification(user, roles, operation)
            
        except Exception as e:
            results['failed'].append({
                'username': user.username,
                'error': str(e)
            })
    
    db.session.commit()
    return results
```

## 2. Email Notifications

### A. Enhanced Email Service

1. Email Templates
```python
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to the System',
        'template': '''
Hello {full_name},

Welcome to the system! Your account has been created with the following details:

Username: {username}
Temporary Password: {temp_password}

Please change your password upon first login.

Best regards,
System Admin
        '''
    },
    'role_update': {
        'subject': 'Role Update Notification',
        'template': '''
Hello {full_name},

Your roles have been updated:

{role_changes}

If you believe this is an error, please contact your administrator.

Best regards,
System Admin
        '''
    },
    'system_alert': {
        'subject': 'System Alert: {alert_type}',
        'template': '''
Alert: {alert_message}

Time: {timestamp}
Severity: {severity}
Action Required: {action_required}

System Administrator
        '''
    }
}

def send_templated_email(template_name, recipient, **kwargs):
    """Send an email using a predefined template."""
    template = EMAIL_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Email template '{template_name}' not found")
    
    subject = template['subject'].format(**kwargs)
    body = template['template'].format(**kwargs)
    
    send_notification_email(subject, body, [recipient])
```

2. Implementation in User Management
```python
def send_welcome_email(user, temp_password):
    """Send welcome email to new user."""
    send_templated_email(
        'welcome',
        user.email,
        full_name=user.full_name or user.username,
        username=user.username,
        temp_password=temp_password
    )

def send_role_update_notification(user, roles, operation):
    """Send notification about role changes."""
    role_changes = f"Roles {operation}ed: {', '.join(r.name for r in roles)}"
    
    send_templated_email(
        'role_update',
        user.email,
        full_name=user.full_name or user.username,
        role_changes=role_changes
    )
```

## Implementation Priority

### Immediate Tasks
1. Implement CSV import/export functionality
2. Set up email templates
3. Add batch role assignment

### Short-term Tasks
1. Enhance error handling and validation
2. Add progress tracking for bulk operations
3. Implement email queue system

### Long-term Tasks
1. Advanced user import options
2. Custom email template editor
3. Scheduled bulk operations

## Technical Notes

1. Database Considerations:
- Batch operation logging
- Email notification tracking
- Operation history

2. Performance Optimization:
- Chunk large imports
- Async email sending
- Background task processing

3. Security Measures:
- CSV validation
- Rate limiting
- Audit logging

## Testing Strategy

1. Unit Tests:
- CSV processing
- Email template rendering
- Batch role operations

2. Integration Tests:
- End-to-end import process
- Email sending
- Role assignment

3. Performance Tests:
- Large CSV imports
- Bulk email sending
- Concurrent operations

## Migration Plan

1. Database Updates:
```sql
-- Add email notification tracking
CREATE TABLE email_notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    template_name VARCHAR(64) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Add batch operation logging
CREATE TABLE batch_operations (
    id INTEGER PRIMARY KEY,
    operation_type VARCHAR(64) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    results JSON,
    initiated_by INTEGER NOT NULL,
    FOREIGN KEY (initiated_by) REFERENCES user(id)
);
```

2. Configuration Updates:
- Email template directory
- CSV upload directory
- Batch operation settings

## Security Considerations

1. Data Protection:
- CSV data validation
- Email content sanitization
- Temporary password handling

2. Access Control:
- Bulk operation permissions
- Email template access
- Operation logging

3. Rate Limiting:
- Bulk import limits
- Email sending quotas
- API request limits
