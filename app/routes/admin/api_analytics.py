"""API endpoints for analytics dashboard."""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.analytics_service import analytics_service
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

def init_analytics_api_routes(bp):
    """Initialize analytics API routes."""
    
    @bp.route('/api/analytics/overview')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_analytics_overview():
        """Get overview of all analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            
            # Get all reports
            feature_usage = analytics_service.get_feature_usage_report(days)
            document_analytics = analytics_service.get_document_analytics_report(days)
            project_performance = analytics_service.get_project_performance_report(days=days)
            team_productivity = analytics_service.get_team_productivity_report(days=days)
            resource_utilization = analytics_service.get_resource_utilization_report(days=days)
            
            return jsonify({
                'success': True,
                'data': {
                    'feature_usage': feature_usage,
                    'document_analytics': document_analytics,
                    'project_performance': project_performance,
                    'team_productivity': team_productivity,
                    'resource_utilization': resource_utilization
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting analytics overview: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/features')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_feature_analytics():
        """Get feature usage analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            report = analytics_service.get_feature_usage_report(days)
            
            return jsonify({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error getting feature analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/documents')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_document_analytics():
        """Get document analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            report = analytics_service.get_document_analytics_report(days)
            
            return jsonify({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error getting document analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/projects')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_project_analytics():
        """Get project performance analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            project_id = request.args.get('project_id', type=int)
            
            report = analytics_service.get_project_performance_report(
                project_id=project_id,
                days=days
            )
            
            return jsonify({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error getting project analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/teams')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_team_analytics():
        """Get team productivity analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            team_id = request.args.get('team_id', type=int)
            
            report = analytics_service.get_team_productivity_report(
                team_id=team_id,
                days=days
            )
            
            return jsonify({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error getting team analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/resources')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def get_resource_analytics():
        """Get resource utilization analytics."""
        try:
            days = request.args.get('days', default=30, type=int)
            resource_type = request.args.get('resource_type')
            
            report = analytics_service.get_resource_utilization_report(
                resource_type=resource_type,
                days=days
            )
            
            return jsonify({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"Error getting resource analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/analytics/export')
    @login_required
    @requires_permission('admin_analytics_access', 'read')
    def export_analytics():
        """Export analytics data."""
        try:
            report_type = request.args.get('type', 'all')
            days = request.args.get('days', default=30, type=int)
            
            # Get requested report data
            data = {}
            if report_type == 'all' or report_type == 'features':
                data['feature_usage'] = analytics_service.get_feature_usage_report(days)
            if report_type == 'all' or report_type == 'documents':
                data['document_analytics'] = analytics_service.get_document_analytics_report(days)
            if report_type == 'all' or report_type == 'projects':
                data['project_performance'] = analytics_service.get_project_performance_report(days=days)
            if report_type == 'all' or report_type == 'teams':
                data['team_productivity'] = analytics_service.get_team_productivity_report(days=days)
            if report_type == 'all' or report_type == 'resources':
                data['resource_utilization'] = analytics_service.get_resource_utilization_report(days=days)
            
            return jsonify({
                'success': True,
                'data': data,
                'export_date': datetime.utcnow().isoformat(),
                'period_days': days
            })
            
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
