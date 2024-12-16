"""Route handlers for the handoffs plugin."""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db, csrf
from app.plugins.handoffs import bp, plugin
from app.plugins.handoffs.models import Handoff, HandoffShift
from app.plugins.handoffs.forms import HandoffForm
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler

logger = plugin.logger

def register_routes(blueprint):
    """Register routes with the provided blueprint."""
    global bp
    bp = blueprint

    @bp.route('/')
    @login_required
    @requires_permission('handoffs_access', 'read')
    @plugin_error_handler
    def index():
        """Display all handoffs with open ones at the top."""
        open_handoffs = Handoff.query.filter_by(status='open').order_by(Handoff.created_at.desc()).all()
        closed_handoffs = Handoff.query.filter_by(status='closed').order_by(Handoff.created_at.desc()).all()
        
        plugin.log_action('view_handoffs', {
            'open_count': len(open_handoffs),
            'closed_count': len(closed_handoffs)
        })
        
        return render_template('handoffs/index.html', 
                             open_handoffs=open_handoffs,
                             closed_handoffs=closed_handoffs)

    @bp.route('/metrics')
    @login_required
    @requires_permission('handoffs_metrics', 'read')
    @plugin_error_handler
    def metrics():
        """Display handoff metrics and statistics."""
        # Calculate time ranges
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Basic counts
        total_handoffs = Handoff.query.count()
        open_handoffs = Handoff.query.filter_by(status='open').count()
        
        # Calculate average time to close
        closed_handoffs = Handoff.query.filter(
            Handoff.status == 'closed',
            Handoff.closed_at.isnot(None)
        ).all()
        
        if closed_handoffs:
            total_hours = sum(
                (h.closed_at - h.created_at).total_seconds() / 3600 
                for h in closed_handoffs
            )
            avg_time_to_close = round(total_hours / len(closed_handoffs), 1)
        else:
            avg_time_to_close = 0

        # Calculate completion rate for last 30 days
        month_handoffs = Handoff.query.filter(Handoff.created_at >= month_ago).all()
        if month_handoffs:
            completed = sum(1 for h in month_handoffs if h.status == 'closed')
            completion_rate = round((completed / len(month_handoffs)) * 100)
        else:
            completion_rate = 0

        # Priority distribution
        priority_counts = db.session.query(
            Handoff.priority, 
            func.count(Handoff.id)
        ).group_by(Handoff.priority).all()
        
        priority_data = [
            sum(count for pri, count in priority_counts if pri == 'high'),
            sum(count for pri, count in priority_counts if pri == 'medium'),
            sum(count for pri, count in priority_counts if pri == 'low')
        ]

        # Shift distribution
        shifts = HandoffShift.query.all()
        shift_labels = [shift.name for shift in shifts]
        shift_data = [
            Handoff.query.filter_by(assigned_to=shift.name).count()
            for shift in shifts
        ]

        # Trend data for the last 30 days
        trend_labels = []
        trend_data = {'open': [], 'closed': []}
        
        for i in range(30, -1, -1):
            date = now - timedelta(days=i)
            trend_labels.append(date.strftime('%Y-%m-%d'))
            
            open_count = Handoff.query.filter(
                Handoff.status == 'open',
                func.date(Handoff.created_at) == date.date()
            ).count()
            
            closed_count = Handoff.query.filter(
                Handoff.status == 'closed',
                func.date(Handoff.closed_at) == date.date()
            ).count()
            
            trend_data['open'].append(open_count)
            trend_data['closed'].append(closed_count)

        # Detailed statistics
        def get_stats_for_period(start_date):
            period_handoffs = Handoff.query.filter(Handoff.created_at >= start_date).all()
            if not period_handoffs:
                return {
                    'total': 0, 'high': 0, 'medium': 0, 'low': 0, 'avg_time': 0
                }
            
            closed = [h for h in period_handoffs if h.status == 'closed' and h.closed_at]
            avg_time = round(sum(
                (h.closed_at - h.created_at).total_seconds() / 3600 
                for h in closed
            ) / len(closed), 1) if closed else 0
            
            return {
                'total': len(period_handoffs),
                'high': sum(1 for h in period_handoffs if h.priority == 'high'),
                'medium': sum(1 for h in period_handoffs if h.priority == 'medium'),
                'low': sum(1 for h in period_handoffs if h.priority == 'low'),
                'avg_time': avg_time
            }

        stats = {
            'day': get_stats_for_period(day_ago),
            'week': get_stats_for_period(week_ago),
            'month': get_stats_for_period(month_ago),
            'all_time': get_stats_for_period(datetime.min)
        }
        
        plugin.log_action('view_metrics', {
            'total_handoffs': total_handoffs,
            'open_handoffs': open_handoffs,
            'avg_time_to_close': avg_time_to_close,
            'completion_rate': completion_rate
        })

        return render_template('handoffs/metrics.html',
                             total_handoffs=total_handoffs,
                             open_handoffs=open_handoffs,
                             avg_time_to_close=avg_time_to_close,
                             completion_rate=completion_rate,
                             priority_data=priority_data,
                             shift_labels=shift_labels,
                             shift_data=shift_data,
                             trend_labels=trend_labels,
                             trend_data=trend_data,
                             stats=stats)

    @bp.route('/create', methods=['GET', 'POST'])
    @login_required
    @requires_permission('handoffs_create', 'write')
    @plugin_error_handler
    def create():
        """Create a new handoff."""
        form = HandoffForm()
        
        if request.method == 'POST':
            # Get the raw datetime value from the form
            raw_due_date = request.form.get('due_date')
            if raw_due_date:
                try:
                    # Parse the datetime from the HTML5 datetime-local format
                    form.due_date.data = datetime.strptime(raw_due_date, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Invalid date format. Please use the date picker.', 'error')
                    return render_template('handoffs/create.html', form=form)
        
        if form.validate_on_submit():
            handoff = Handoff(
                reporter_id=current_user.id,
                assigned_to=form.assigned_to.data,
                priority=form.priority.data,
                ticket=form.ticket.data,
                hostname=form.hostname.data,
                kirke=form.kirke.data,
                due_date=form.due_date.data,
                has_bridge=form.has_bridge.data,
                bridge_link=form.bridge_link.data if form.has_bridge.data else None,
                description=form.description.data,
                status='open'
            )
            db.session.add(handoff)
            db.session.commit()
            
            plugin.log_action('create_handoff', {
                'handoff_id': handoff.id,
                'assigned_to': handoff.assigned_to,
                'priority': handoff.priority
            })
            
            flash('Handoff created successfully.', 'success')
            return redirect(url_for('handoffs.index'))
        
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
        
        return render_template('handoffs/create.html', form=form)

    @bp.route('/<int:id>/close', methods=['POST'])
    @login_required
    @requires_permission('handoffs_close', 'write')
    @plugin_error_handler
    def close_handoff(id):
        """Close a handoff."""
        handoff = Handoff.query.get_or_404(id)
        if handoff.status == 'open':
            handoff.status = 'closed'
            handoff.closed_at = datetime.utcnow()
            db.session.commit()
            
            plugin.log_action('close_handoff', {
                'handoff_id': handoff.id,
                'time_to_close': (handoff.closed_at - handoff.created_at).total_seconds() / 3600
            })
            
            return jsonify({
                'status': 'success',
                'message': 'Handoff closed successfully',
                'handoff_id': handoff.id
            })
            
        return jsonify({
            'status': 'error',
            'message': 'Handoff is already closed'
        }), 400
