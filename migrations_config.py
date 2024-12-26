from flask import Flask
from flask_migrate import Migrate
from app.extensions import db

# Import only core models needed for initial migration
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.permissions import Action, RoutePermission
from app.models.activity import UserActivity, PageVisit

# Import models that don't have Vault dependencies
from app.models.navigation import NavigationCategory, PageRouteMapping
from app.models.documents import Document, DocumentCategory, DocumentTag
from app.models.metrics import Metric, MetricAlert, MetricDashboard
from app.models.analytics import FeatureUsage, DocumentAnalytics, ProjectMetrics

# Basic plugin models without Vault dependencies
from app.blueprints.projects.models import ProjectStatus, ProjectPriority, Project, Task, Todo, Comment, History
from app.blueprints.bug_reports.models import BugReport, BugReportScreenshot
from app.blueprints.feature_requests.models import FeatureRequest, FeatureVote, FeatureComment
from app.blueprints.weblinks.models import WebLink, Tag, WebLinkHistory

import os

# Create instance directory if it doesn't exist
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Create minimal Flask app for migrations
app = Flask(__name__, instance_path=instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'app.db')}"
app.config['SECRET_KEY'] = "packaging-key"
db.init_app(app)
migrate = Migrate(app, db)

# Ensure instance directory has correct permissions
os.chmod(instance_path, 0o755)
