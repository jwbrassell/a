"""Import/Export routes for Weblinks plugin."""

import csv
import tempfile
from datetime import datetime
from io import StringIO
from flask import jsonify, request, make_response
from flask_login import login_required, current_user
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import WebLink, WebLinkCategory, WebLinkTag

def register_routes(bp):
    """Register import/export routes with blueprint."""

    @bp.route('/export/csv')
    @login_required
    @requires_permission('weblinks_import_export', 'read')
    def export_csv():
        """Export links to CSV."""
        try:
            links = WebLink.query.filter_by(deleted_at=None).all()
            
            # Create CSV in memory
            si = StringIO()
            writer = csv.writer(si)
            
            # Write header
            writer.writerow([
                'URL',
                'Friendly Name',
                'Category',
                'Tags',
                'Notes',
                'Icon',
                'Created By',
                'Created At',
                'Updated By',
                'Updated At'
            ])
            
            # Write data
            for link in links:
                writer.writerow([
                    link.url,
                    link.friendly_name,
                    link.category.name if link.category else '',
                    ','.join(tag.name for tag in link.tags),
                    link.notes or '',
                    link.icon or '',
                    link.creator.username,
                    link.created_at.isoformat() if link.created_at else '',
                    link.updater.username,
                    link.updated_at.isoformat() if link.updated_at else ''
                ])
            
            # Create response
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = (
                f"attachment; filename=weblinks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            output.headers["Content-type"] = "text/csv"
            return output
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error exporting CSV: {str(e)}'
            }), 500

    @bp.route('/import/csv', methods=['POST'])
    @login_required
    @requires_permission('weblinks_import_export', 'write')
    def import_csv():
        """Import links from CSV."""
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                file.save(temp_file.name)
                temp_file.seek(0)
                reader = csv.DictReader(temp_file)
                
                imported_count = 0
                skipped_count = 0
                errors = []
                
                for row in reader:
                    try:
                        # Skip if URL already exists
                        if WebLink.query.filter_by(url=row['URL'], deleted_at=None).first():
                            skipped_count += 1
                            continue
                        
                        # Get or create category
                        category = None
                        if row.get('Category'):
                            category = WebLinkCategory.query.filter_by(
                                name=row['Category'],
                                deleted_at=None
                            ).first()
                            if not category:
                                category = WebLinkCategory(
                                    name=row['Category'],
                                    created_by=current_user.id,
                                    updated_by=current_user.id
                                )
                                db.session.add(category)
                        
                        # Create link
                        link = WebLink(
                            url=row['URL'],
                            friendly_name=row['Friendly Name'],
                            notes=row.get('Notes', ''),
                            icon=row.get('Icon', ''),
                            category=category,
                            created_by=current_user.id,
                            updated_by=current_user.id
                        )
                        
                        # Handle tags
                        if row.get('Tags'):
                            tag_names = [t.strip() for t in row['Tags'].split(',')]
                            for tag_name in tag_names:
                                if tag_name:
                                    tag = WebLinkTag.query.filter_by(
                                        name=tag_name,
                                        deleted_at=None
                                    ).first()
                                    if not tag:
                                        tag = WebLinkTag(
                                            name=tag_name,
                                            created_by=current_user.id,
                                            updated_by=current_user.id
                                        )
                                        db.session.add(tag)
                                    link.tags.append(tag)
                        
                        db.session.add(link)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Error importing row {imported_count + skipped_count + 1}: {str(e)}")
                
                if imported_count > 0:
                    db.session.commit()
                
                return jsonify({
                    'success': True,
                    'imported': imported_count,
                    'skipped': skipped_count,
                    'errors': errors
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
