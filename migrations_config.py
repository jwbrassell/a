from flask import Flask
from flask_migrate import Migrate
from app.extensions import db

# Import all models needed for migrations
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.permissions import Action, RoutePermission
from app.models.navigation import NavigationCategory, PageRouteMapping
from app.models.documents import Document, DocumentCategory, DocumentTag
from app.models.metrics import Metric, MetricAlert, MetricDashboard
from app.models.analytics import FeatureUsage, DocumentAnalytics, ProjectMetrics
from app.models.dispatch import DispatchSettings, DispatchHistory
from app.models.handoffs import WorkCenter, WorkCenterMember, HandoffSettings, Handoff
from app.models.activity import UserActivity, PageVisit

# Create minimal Flask app for migrations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SECRET_KEY'] = "packaging-key"
db.init_app(app)
migrate = Migrate(app, db)
