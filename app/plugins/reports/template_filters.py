from datetime import datetime

def format_datetime(value):
    """Format datetime object to string."""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value.strftime('%Y-%m-%d %H:%M:%S')

def register_template_filters(blueprint):
    """Register custom template filters with the blueprint."""
    blueprint.add_app_template_filter(format_datetime, 'format_datetime')
