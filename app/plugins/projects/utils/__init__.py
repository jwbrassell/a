"""Utility functions for the projects plugin."""

from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import json
from .caching import (
    cache,
    init_cache,
    cached_project,
    cached_task,
    cached_project_stats,
    cached_user_projects,
    cached_project_team,
    invalidate_project_cache,
    invalidate_task_cache,
    invalidate_user_cache,
    CacheManager
)
from .monitoring import (
    performance_metrics,
    query_tracker,
    monitor_performance,
    monitor_database,
    monitor_cache,
    monitor_api,
    get_performance_report,
    log_slow_operations
)
from app.extensions import db
from app.plugins.projects.models import ProjectStatus, ProjectPriority

def init_project_settings():
    """Initialize project statuses and priorities if they don't exist."""
    # Default statuses
    default_statuses = [
        ('New', 'primary'),
        ('In Progress', 'info'),
        ('On Hold', 'warning'),
        ('Completed', 'success'),
        ('Cancelled', 'danger'),
        ('Archived', 'secondary')
    ]
    
    # Default priorities
    default_priorities = [
        ('Low', 'success'),
        ('Medium', 'warning'),
        ('High', 'danger')
    ]
    
    # Create statuses
    for name, color in default_statuses:
        if not ProjectStatus.query.filter_by(name=name).first():
            status = ProjectStatus(name=name, color=color)
            db.session.add(status)
    
    # Create priorities
    for name, color in default_priorities:
        if not ProjectPriority.query.filter_by(name=name).first():
            priority = ProjectPriority(name=name, color=color)
            db.session.add(priority)
    
    db.session.commit()

DateType = Union[date, datetime, str]

def serialize_date(date_obj: Optional[DateType]) -> Optional[str]:
    """Convert date/datetime to ISO format string"""
    if not date_obj:
        return None
    if isinstance(date_obj, str):
        return date_obj
    if hasattr(date_obj, 'isoformat'):
        return date_obj.isoformat()
    return None

def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f} minutes"
    hours = minutes / 60
    return f"{hours:.1f} hours"

def calculate_completion_percentage(completed: int, total: int) -> int:
    """Calculate completion percentage"""
    if total == 0:
        return 0
    return round((completed / total) * 100)

def sanitize_html(html: Optional[str]) -> Optional[str]:
    """Sanitize HTML content"""
    if not html:
        return html
    
    import bleach
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'img', 'code', 'pre', 'blockquote',
        'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    allowed_attrs = {
        '*': ['class', 'style'],
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height']
    }
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling dates and special types"""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

def to_json(data: Any) -> str:
    """Convert data to JSON string"""
    return json.dumps(data, cls=JSONEncoder)

def from_json(json_str: str) -> Any:
    """Convert JSON string to data"""
    return json.loads(json_str)

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    import re
    from unidecode import unidecode
    
    # Convert to ASCII
    text = unidecode(text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r'[\s]+', '-', text)
    # Remove all other special characters
    text = re.sub(r'[^\w\-]', '', text)
    # Remove duplicate hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text

def truncate_string(text: str, length: int, suffix: str = '...') -> str:
    """Truncate string to specified length"""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length - len(suffix)].strip() + suffix

def strip_tags(html: str) -> str:
    """Remove HTML tags from string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)

def is_valid_email(email: str) -> bool:
    """Check if string is valid email address"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def get_gravatar_url(email: str, size: int = 80) -> str:
    """Get Gravatar URL for email address"""
    import hashlib
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"

# Export all utility functions
__all__ = [
    # Initialization
    'init_project_settings',
    
    # Caching utilities
    'cache',
    'init_cache',
    'cached_project',
    'cached_task',
    'cached_project_stats',
    'cached_user_projects',
    'cached_project_team',
    'invalidate_project_cache',
    'invalidate_task_cache',
    'invalidate_user_cache',
    'CacheManager',
    
    # Monitoring utilities
    'performance_metrics',
    'query_tracker',
    'monitor_performance',
    'monitor_database',
    'monitor_cache',
    'monitor_api',
    'get_performance_report',
    'log_slow_operations',
    
    # General utilities
    'serialize_date',
    'parse_date',
    'format_duration',
    'calculate_completion_percentage',
    'sanitize_html',
    'format_file_size',
    'JSONEncoder',
    'to_json',
    'from_json',
    'merge_dicts',
    'chunk_list',
    'generate_slug',
    'truncate_string',
    'strip_tags',
    'is_valid_email',
    'get_gravatar_url'
]
