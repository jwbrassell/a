"""
AWS Manager Constants
-------------------
Constants and configuration values used throughout the AWS Manager blueprint.
"""

# AWS Regions list with display names
AWS_REGIONS = [
    {'id': 'us-east-1', 'name': 'US East (N. Virginia)'},
    {'id': 'us-east-2', 'name': 'US East (Ohio)'},
    {'id': 'us-west-1', 'name': 'US West (N. California)'},
    {'id': 'us-west-2', 'name': 'US West (Oregon)'},
    {'id': 'af-south-1', 'name': 'Africa (Cape Town)'},
    {'id': 'ap-east-1', 'name': 'Asia Pacific (Hong Kong)'},
    {'id': 'ap-south-1', 'name': 'Asia Pacific (Mumbai)'},
    {'id': 'ap-northeast-1', 'name': 'Asia Pacific (Tokyo)'},
    {'id': 'ap-northeast-2', 'name': 'Asia Pacific (Seoul)'},
    {'id': 'ap-northeast-3', 'name': 'Asia Pacific (Osaka)'},
    {'id': 'ap-southeast-1', 'name': 'Asia Pacific (Singapore)'},
    {'id': 'ap-southeast-2', 'name': 'Asia Pacific (Sydney)'},
    {'id': 'ca-central-1', 'name': 'Canada (Central)'},
    {'id': 'eu-central-1', 'name': 'Europe (Frankfurt)'},
    {'id': 'eu-west-1', 'name': 'Europe (Ireland)'},
    {'id': 'eu-west-2', 'name': 'Europe (London)'},
    {'id': 'eu-west-3', 'name': 'Europe (Paris)'},
    {'id': 'eu-north-1', 'name': 'Europe (Stockholm)'},
    {'id': 'eu-south-1', 'name': 'Europe (Milan)'},
    {'id': 'me-south-1', 'name': 'Middle East (Bahrain)'},
    {'id': 'sa-east-1', 'name': 'South America (São Paulo)'}
]

# List of region IDs only
AWS_REGION_IDS = [region['id'] for region in AWS_REGIONS]

# Map of region IDs to display names
AWS_REGION_NAMES = {region['id']: region['name'] for region in AWS_REGIONS}

# Common instance types
EC2_INSTANCE_TYPES = [
    't2.micro',
    't2.small',
    't2.medium',
    't3.micro',
    't3.small',
    't3.medium',
    'm5.large',
    'm5.xlarge',
    'c5.large',
    'c5.xlarge',
    'r5.large',
    'r5.xlarge'
]

# Health event severity levels
HEALTH_EVENT_SEVERITY = {
    'critical': 'Critical',
    'warning': 'Warning',
    'info': 'Information'
}

# Health event types
HEALTH_EVENT_TYPES = [
    'issue',
    'scheduledChange',
    'accountNotification'
]
