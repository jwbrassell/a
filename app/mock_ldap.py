from datetime import datetime
import os
import string
import random

class MockLDAPUser:
    """Sample user data structure matching LDAP response."""
    def __init__(self, username, employee_number, name, email, vzid):
        self.username = username
        self.employee_number = employee_number
        self.name = name
        self.email = email
        self.vzid = vzid
        self.password = self._generate_password()
        self.created_at = datetime.utcnow()

    def _generate_password(self):
        """Generate a simple password for testing."""
        return 'test123'  # Fixed password for easy testing

    def to_dict(self):
        """Convert user data to dictionary format matching LDAP response."""
        return {
            'username': self.username,
            'employee_number': self.employee_number,
            'name': self.name,
            'email': self.email,
            'vzid': self.vzid
        }

# Generate sample users
SAMPLE_USERS = [
    MockLDAPUser(
        username='admin',
        employee_number='EMP001',
        name='Admin User',
        email='admin@example.com',
        vzid='VZ001'
    ),
    MockLDAPUser(
        username='manager',  # This user will get manager role
        employee_number='EMP002',
        name='Team Manager',
        email='manager@example.com',
        vzid='VZ002'
    ),
    MockLDAPUser(
        username='developer',  # This user will get developer role
        employee_number='EMP003',
        name='Development User',
        email='developer@example.com',
        vzid='VZ003'
    ),
    MockLDAPUser(
        username='support',
        employee_number='EMP004',
        name='Support User',
        email='support@example.com',
        vzid='VZ004'
    ),
    MockLDAPUser(
        username='operator',
        employee_number='EMP005',
        name='Operations User',
        email='operator@example.com',
        vzid='VZ005'
    ),
    MockLDAPUser(
        username='security',
        employee_number='EMP006',
        name='Security User',
        email='security@example.com',
        vzid='VZ006'
    ),
    MockLDAPUser(
        username='netadmin',
        employee_number='EMP007',
        name='Network Admin User',
        email='netadmin@example.com',
        vzid='VZ007'
    ),
    MockLDAPUser(
        username='devops',
        employee_number='EMP008',
        name='DevOps User',
        email='devops@example.com',
        vzid='VZ008'
    ),
    MockLDAPUser(
        username='helpdesk',
        employee_number='EMP009',
        name='Helpdesk User',
        email='helpdesk@example.com',
        vzid='VZ009'
    ),
    MockLDAPUser(
        username='demo',  # Added demo user
        employee_number='EMP010',
        name='Demo User',
        email='demo@example.com',
        vzid='VZ010'
    )
]

# Store users by username for quick lookup
USER_DB = {user.username: user for user in SAMPLE_USERS}

def authenticate_ldap(username, password, vault_addr=None, vault_token=None, application=None):
    """Mock LDAP authentication function."""
    print(f"Mock LDAP: Attempting authentication for user: {username}")  # Debug log
    user = USER_DB.get(username)
    if user and password == 'test123':  # Fixed password for all users
        print(f"Mock LDAP: Authentication successful for user: {username}")  # Debug log
        return user.to_dict()
    print(f"Mock LDAP: Authentication failed for user: {username}")  # Debug log
    return None

def generate_credentials_file():
    """Generate a file with all user credentials."""
    content = ["=== Sample User Credentials ===\n"]
    content.append("Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
    content.append("All users have password: test123\n\n")
    
    content.append("Available Users:\n")
    for user in SAMPLE_USERS:
        content.extend([
            f"Username: {user.username}",
            f"Name: {user.name}",
            f"Email: {user.email}",
            f"Employee #: {user.employee_number}",
            f"VZ ID: {user.vzid}",
            "-" * 50 + "\n"
        ])
    
    return "\n".join(content)

# Generate credentials file on module import
try:
    os.makedirs('instance', exist_ok=True)
    credentials_content = generate_credentials_file()
    
    # Write to file
    with open('instance/user_credentials.txt', 'w') as f:
        f.write(credentials_content)
    
    # Print to console
    print("\n=== Mock LDAP Users ===")
    print("All users have password: test123")
    print("Available usernames:", ", ".join(USER_DB.keys()))
    print("Full credentials written to: instance/user_credentials.txt")
except Exception as e:
    print(f"Error generating credentials file: {e}")

# If running directly, print all credentials
if __name__ == '__main__':
    print(generate_credentials_file())
