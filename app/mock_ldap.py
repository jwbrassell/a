"""Mock LDAP implementation for development and testing."""

class MockLDAP:
    """Simulates LDAP functionality for development and testing."""
    
    def __init__(self):
        # Simulate LDAP groups and their members
        self._groups = {
            'cn=admins,dc=example,dc=com': ['admin'],
            'cn=managers,dc=example,dc=com': ['manager'],
            'cn=developers,dc=example,dc=com': ['developer'],
            'cn=support,dc=example,dc=com': ['support'],
            'cn=operators,dc=example,dc=com': ['operator'],
            'cn=security,dc=example,dc=com': ['security'],
            'cn=netadmins,dc=example,dc=com': ['netadmin'],
            'cn=devops,dc=example,dc=com': ['devops'],
            'cn=helpdesk,dc=example,dc=com': ['helpdesk'],
            'cn=users,dc=example,dc=com': [
                'admin', 'manager', 'developer', 'support', 
                'operator', 'security', 'netadmin', 'devops', 
                'helpdesk', 'demo'
            ]
        }
        
        # Simulate user attributes
        self._users = {
            'admin': {
                'cn': 'Admin User',
                'mail': 'admin@example.com',
                'memberOf': ['cn=admins,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E001',
                'name': 'Admin User',
                'email': 'admin@example.com',
                'vzid': 'admin001'
            },
            'manager': {
                'cn': 'Manager User',
                'mail': 'manager@example.com',
                'memberOf': ['cn=managers,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E002',
                'name': 'Manager User',
                'email': 'manager@example.com',
                'vzid': 'manager001'
            },
            'developer': {
                'cn': 'Developer User',
                'mail': 'developer@example.com',
                'memberOf': ['cn=developers,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E003',
                'name': 'Developer User',
                'email': 'developer@example.com',
                'vzid': 'dev001'
            },
            'support': {
                'cn': 'Support User',
                'mail': 'support@example.com',
                'memberOf': ['cn=support,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E004',
                'name': 'Support User',
                'email': 'support@example.com',
                'vzid': 'support001'
            },
            'operator': {
                'cn': 'Operator User',
                'mail': 'operator@example.com',
                'memberOf': ['cn=operators,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E005',
                'name': 'Operator User',
                'email': 'operator@example.com',
                'vzid': 'op001'
            },
            'security': {
                'cn': 'Security User',
                'mail': 'security@example.com',
                'memberOf': ['cn=security,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E006',
                'name': 'Security User',
                'email': 'security@example.com',
                'vzid': 'sec001'
            },
            'netadmin': {
                'cn': 'Network Admin User',
                'mail': 'netadmin@example.com',
                'memberOf': ['cn=netadmins,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E007',
                'name': 'Network Admin User',
                'email': 'netadmin@example.com',
                'vzid': 'net001'
            },
            'devops': {
                'cn': 'DevOps User',
                'mail': 'devops@example.com',
                'memberOf': ['cn=devops,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E008',
                'name': 'DevOps User',
                'email': 'devops@example.com',
                'vzid': 'devops001'
            },
            'helpdesk': {
                'cn': 'Helpdesk User',
                'mail': 'helpdesk@example.com',
                'memberOf': ['cn=helpdesk,dc=example,dc=com', 'cn=users,dc=example,dc=com'],
                'employee_number': 'E009',
                'name': 'Helpdesk User',
                'email': 'helpdesk@example.com',
                'vzid': 'help001'
            },
            'demo': {
                'cn': 'Demo User',
                'mail': 'demo@example.com',
                'memberOf': ['cn=users,dc=example,dc=com'],
                'employee_number': 'E010',
                'name': 'Demo User',
                'email': 'demo@example.com',
                'vzid': 'demo001'
            }
        }
    
    def get_groups(self) -> list:
        """Get all available LDAP groups."""
        return list(self._groups.keys())
    
    def get_group_members(self, group: str) -> list:
        """Get all members of a specific LDAP group."""
        return self._groups.get(group, [])
    
    def get_user_groups(self, username: str) -> list:
        """Get all groups a user belongs to."""
        return self._users.get(username, {}).get('memberOf', [])
    
    def get_user_info(self, username: str) -> dict:
        """Get user information from LDAP."""
        return self._users.get(username, {})
    
    def authenticate(self, username: str, password: str) -> bool:
        """Mock LDAP authentication."""
        # In development, accept any user in our mock data with password 'test123'
        return username in self._users and password == 'test123'
    
    def search_users(self, query: str) -> list:
        """Search for users in LDAP."""
        query = query.lower()
        return [
            username for username, data in self._users.items()
            if query in username.lower() or 
               query in data['cn'].lower() or 
               query in data['mail'].lower()
        ]
    
    def is_member_of(self, username: str, group: str) -> bool:
        """Check if a user is a member of a specific group."""
        return username in self._groups.get(group, [])
    
    def get_all_users(self) -> list:
        """Get all users in LDAP."""
        return list(self._users.keys())
    
    def get_group_info(self, group: str) -> dict:
        """Get information about a specific LDAP group."""
        if group not in self._groups:
            return None
        
        return {
            'dn': group,
            'member_count': len(self._groups[group]),
            'members': self._groups[group]
        }

# Standalone functions for backward compatibility
_ldap = MockLDAP()

def authenticate_ldap(username: str, password: str) -> dict:
    """Authenticate user against LDAP and return user info."""
    if _ldap.authenticate(username, password):
        user_info = _ldap.get_user_info(username)
        if user_info:
            return {
                'username': username,
                'employee_number': user_info.get('employee_number'),
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'vzid': user_info.get('vzid')
            }
    return None

def get_ldap_groups() -> list:
    """Get all available LDAP groups."""
    return _ldap.get_groups()

def get_ldap_group_members(group: str) -> list:
    """Get all members of a specific LDAP group."""
    return _ldap.get_group_members(group)

def get_ldap_user_groups(username: str) -> list:
    """Get all groups a user belongs to."""
    return _ldap.get_user_groups(username)

def get_ldap_user_info(username: str) -> dict:
    """Get user information from LDAP."""
    return _ldap.get_user_info(username)
