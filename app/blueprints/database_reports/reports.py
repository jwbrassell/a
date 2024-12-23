from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
import json
from . import bp
from .models import DatabaseConnection, Report, ReportTagModel as Tag
from app.extensions import db
from .utils import format_value, execute_query, validate_sql_query

@bp.route('/')
@login_required
def index():
    """Dashboard showing all accessible reports"""
    # Get all reports accessible to the user
    reports = Report.query.filter(
        (Report.is_public == True) | (Report.created_by_id == current_user.id)
    ).all()
    
    # Get all unique tags for the filter dropdown
    tags = Tag.query.join(Tag.reports).filter(
        (Report.is_public == True) | (Report.created_by_id == current_user.id)
    ).distinct().all()
    
    return render_template('database_reports/reports/index.html', reports=reports, tags=tags)

@bp.route('/reports/new', methods=['GET', 'POST'])
@login_required
def new_report():
    """Create a new report"""
    if request.method == 'GET':
        connections = DatabaseConnection.query.all()
        return render_template('database_reports/reports/new.html', connections=connections)
    
    # Handle POST request
    try:
        # Validate SQL query
        query = request.form.get('sql_query', '').strip()
        validate_sql_query(query)
        
        report = Report(
            title=request.form['title'],
            description=request.form['description'],
            connection_id=request.form['connection_id'],
            query_config={'sql': query},
            column_config=json.loads(request.form['column_config']),
            is_public=request.form.get('is_public', False),
            created_by_id=current_user.id
        )
        
        # Handle tags
        tags = request.form.get('tags', '').split(',')
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                report.tags.append(tag)
        
        db.session.add(report)
        db.session.commit()
        
        flash('Report created successfully', 'success')
        return redirect(url_for('database_reports.view_report', id=report.id))
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('database_reports.new_report'))
    except Exception as e:
        flash(f'Error creating report: {str(e)}', 'error')
        return redirect(url_for('database_reports.new_report'))

@bp.route('/reports/<int:id>')
@login_required
def view_report(id):
    """View a report"""
    report = Report.query.get_or_404(id)
    
    # Check permissions
    if not report.is_public and report.created_by_id != current_user.id:
        abort(403)
    
    try:
        # Execute report query
        columns, raw_data = execute_query(report.connection, report.query_config['sql'])
        
        # Apply column transformations
        data = []
        for row in raw_data:
            transformed_row = {}
            for i, value in enumerate(row):
                col_name = columns[i]
                col_config = report.column_config.get(col_name, {})
                transformed_row[col_name] = format_value(value, col_config.get('format', 'text'))
            data.append(transformed_row)
        
        return render_template(
            'database_reports/reports/view.html',
            report=report,
            columns=columns,
            data=data
        )
        
    except Exception as e:
        flash(f'Error executing report: {str(e)}', 'error')
        return redirect(url_for('database_reports.index'))

@bp.route('/reports/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    """Edit a report"""
    report = Report.query.get_or_404(id)
    
    # Check permissions
    if report.created_by_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        try:
            # Validate SQL query
            query = request.form.get('sql_query', '').strip()
            validate_sql_query(query)
            
            report.title = request.form['title']
            report.description = request.form['description']
            report.query_config = {'sql': query}
            report.column_config = json.loads(request.form['column_config'])
            report.is_public = request.form.get('is_public', False)
            
            # Update tags
            report.tags = []
            tags = request.form.get('tags', '').split(',')
            for tag_name in tags:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    report.tags.append(tag)
            
            db.session.commit()
            flash('Report updated successfully', 'success')
            return redirect(url_for('database_reports.view_report', id=report.id))
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Error updating report: {str(e)}', 'error')
    
    return render_template('database_reports/reports/edit.html', report=report)

@bp.route('/reports/search')
@login_required
def search_reports():
    """Search reports"""
    query = request.args.get('q', '').strip()
    tag = request.args.get('tag')
    
    reports = Report.query
    
    # Filter by search query
    if query:
        reports = reports.filter(
            (Report.title.ilike(f'%{query}%')) |
            (Report.description.ilike(f'%{query}%'))
        )
    
    # Filter by tag
    if tag:
        reports = reports.join(Report.tags).filter(Tag.name == tag)
    
    # Filter by permissions
    reports = reports.filter(
        (Report.is_public == True) | (Report.created_by_id == current_user.id)
    )
    
    # Get all unique tags for the filter dropdown
    tags = Tag.query.join(Tag.reports).filter(
        (Report.is_public == True) | (Report.created_by_id == current_user.id)
    ).distinct().all()
    
    return render_template(
        'database_reports/reports/search.html',
        reports=reports.all(),
        query=query,
        tag=tag,
        tags=tags
    )
