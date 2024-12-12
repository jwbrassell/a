from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from io import BytesIO
from app import db
from app.plugins.documents import bp
from app.plugins.documents.models import (
    Document, DocumentCategory, DocumentTag, DocumentChange,
    DocumentShare, DocumentCache
)
from app.plugins.documents.forms import (
    DocumentForm, CategoryForm, TagForm, DocumentShareForm,
    DocumentSearchForm, BulkActionForm, DocumentFromTemplateForm
)
from app.plugins.documents.utils import (
    get_or_create_cache, bulk_categorize, bulk_delete
)
from app.models import User

@bp.route('/')
@login_required
def index():
    """Display main documents page."""
    # Get documents user has access to
    documents = Document.query.filter(
        or_(
            Document.is_private == False,
            Document.created_by == current_user.id,
            Document.shared_with.any(DocumentShare.user_id == current_user.id)
        )
    ).order_by(Document.updated_at.desc()).all()
    
    categories = DocumentCategory.query.all()
    bulk_form = BulkActionForm()
    bulk_form.category.choices = [(c.id, c.name) for c in categories]
    bulk_form.user.choices = [(u.id, u.username) for u in User.query.all()]
    
    return render_template('documents/index.html',
                         documents=documents,
                         categories=categories,
                         bulk_form=bulk_form)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new document."""
    form = DocumentForm()
    
    # Populate category and tag choices
    categories = DocumentCategory.query.all()
    form.category.choices = [(c.id, c.name) for c in categories]
    tags = DocumentTag.query.all()
    form.tags.choices = [(t.id, t.name) for t in tags]
    
    if form.validate_on_submit():
        try:
            # Handle new category if provided
            category_id = form.category.data
            if form.new_category.data:
                new_category = DocumentCategory(name=form.new_category.data)
                db.session.add(new_category)
                db.session.flush()
                category_id = new_category.id
            
            # Create document
            document = Document(
                title=form.title.data,
                content=form.content.data,
                category_id=category_id,
                created_by=current_user.id,
                is_template=form.is_template.data,
                template_name=form.template_name.data if form.is_template.data else None,
                is_private=form.is_private.data
            )
            db.session.add(document)
            
            # Handle existing tags
            if form.tags.data:
                selected_tags = DocumentTag.query.filter(DocumentTag.id.in_(form.tags.data)).all()
                document.tags.extend(selected_tags)
            
            # Handle new tags
            if form.new_tags.data:
                new_tag_names = [t.strip() for t in form.new_tags.data.split(',')]
                for tag_name in new_tag_names:
                    if tag_name:
                        tag = DocumentTag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = DocumentTag(name=tag_name)
                            db.session.add(tag)
                            db.session.flush()
                        document.tags.append(tag)
            
            # Record the creation
            change = DocumentChange(
                document=document,
                changed_by=current_user.id,
                change_type='create'
            )
            db.session.add(change)
            
            db.session.commit()
            flash('Document created successfully.', 'success')
            return redirect(url_for('documents.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating document: {str(e)}', 'error')
    
    return render_template('documents/create.html', form=form)

@bp.route('/create-from-template', methods=['GET', 'POST'])
@login_required
def create_from_template():
    """Create a new document from a template."""
    form = DocumentFromTemplateForm()
    
    # Populate choices
    templates = Document.query.filter_by(is_template=True).all()
    form.template.choices = [(t.id, t.template_name or t.title) for t in templates]
    categories = DocumentCategory.query.all()
    form.category.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        try:
            template = Document.query.get_or_404(form.template.data)
            
            document = Document(
                title=form.title.data,
                content=template.content,
                category_id=form.category.data,
                created_by=current_user.id,
                is_private=form.is_private.data
            )
            db.session.add(document)
            
            # Copy tags from template
            document.tags = template.tags
            
            # Record creation
            change = DocumentChange(
                document=document,
                changed_by=current_user.id,
                change_type='create'
            )
            db.session.add(change)
            
            db.session.commit()
            flash('Document created from template successfully.', 'success')
            return redirect(url_for('documents.edit', id=document.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating document: {str(e)}', 'error')
    
    return render_template('documents/create_from_template.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing document."""
    document = Document.query.get_or_404(id)
    
    # Check permissions
    if not document.user_can_edit(current_user):
        flash('You do not have permission to edit this document.', 'error')
        return redirect(url_for('documents.index'))
    
    form = DocumentForm(obj=document)
    
    # Populate category and tag choices
    categories = DocumentCategory.query.all()
    form.category.choices = [(c.id, c.name) for c in categories]
    tags = DocumentTag.query.all()
    form.tags.choices = [(t.id, t.name) for t in tags]
    
    if request.method == 'GET':
        form.tags.data = [tag.id for tag in document.tags]
    
    if form.validate_on_submit():
        try:
            # Store previous content for history
            previous_content = document.content
            
            # Handle new category if provided
            if form.new_category.data:
                new_category = DocumentCategory(name=form.new_category.data)
                db.session.add(new_category)
                db.session.flush()
                document.category_id = new_category.id
            else:
                document.category_id = form.category.data
            
            document.title = form.title.data
            document.content = form.content.data
            document.is_template = form.is_template.data
            document.template_name = form.template_name.data if form.is_template.data else None
            document.is_private = form.is_private.data
            
            # Handle existing tags
            document.tags = []
            if form.tags.data:
                selected_tags = DocumentTag.query.filter(DocumentTag.id.in_(form.tags.data)).all()
                document.tags.extend(selected_tags)
            
            # Handle new tags
            if form.new_tags.data:
                new_tag_names = [t.strip() for t in form.new_tags.data.split(',')]
                for tag_name in new_tag_names:
                    if tag_name:
                        tag = DocumentTag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = DocumentTag(name=tag_name)
                            db.session.add(tag)
                            db.session.flush()
                        document.tags.append(tag)
            
            # Record the change
            change = DocumentChange(
                document=document,
                changed_by=current_user.id,
                change_type='update',
                previous_content=previous_content
            )
            db.session.add(change)
            
            # Clear any existing caches
            DocumentCache.query.filter_by(document_id=document.id).delete()
            
            db.session.commit()
            flash('Document updated successfully.', 'success')
            return redirect(url_for('documents.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating document: {str(e)}', 'error')
    
    return render_template('documents/edit.html', form=form, document=document)

@bp.route('/search')
@login_required
def search():
    """Search documents."""
    form = DocumentSearchForm(request.args)
    
    # Populate form choices
    categories = DocumentCategory.query.all()
    form.category.choices = [('', 'All Categories')] + [(str(c.id), c.name) for c in categories]
    tags = DocumentTag.query.all()
    form.tags.choices = [(str(t.id), t.name) for t in tags]
    
    # Build query
    query = Document.query.filter(
        or_(
            Document.is_private == False,
            Document.created_by == current_user.id,
            Document.shared_with.any(DocumentShare.user_id == current_user.id)
        )
    )
    
    if form.query.data:
        search_term = f'%{form.query.data}%'
        query = query.filter(
            or_(
                Document.title.ilike(search_term),
                Document.content.ilike(search_term)
            )
        )
    
    if form.category.data:
        query = query.filter_by(category_id=form.category.data)
    
    if form.tags.data:
        for tag_id in form.tags.data:
            query = query.filter(Document.tags.any(id=tag_id))
    
    if form.template_only.data:
        query = query.filter_by(is_template=True)
    
    if form.date_range.data:
        if form.date_range.data == 'today':
            query = query.filter(Document.created_at >= datetime.utcnow().date())
        elif form.date_range.data == 'week':
            query = query.filter(Document.created_at >= datetime.utcnow() - timedelta(days=7))
        elif form.date_range.data == 'month':
            query = query.filter(Document.created_at >= datetime.utcnow() - timedelta(days=30))
        elif form.date_range.data == 'year':
            query = query.filter(Document.created_at >= datetime.utcnow() - timedelta(days=365))
    
    documents = query.order_by(Document.updated_at.desc()).all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([doc.to_dict() for doc in documents])
    
    return render_template('documents/search.html',
                         form=form,
                         documents=documents)

@bp.route('/<int:id>/share', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share document with other users."""
    document = Document.query.get_or_404(id)
    
    # Check permissions
    if document.created_by != current_user.id:
        flash('Only the document owner can share it.', 'error')
        return redirect(url_for('documents.index'))
    
    form = DocumentShareForm()
    form.user.choices = [(u.id, u.username) for u in User.query.filter(User.id != current_user.id).all()]
    
    if form.validate_on_submit():
        try:
            # Check if already shared with user
            existing_share = DocumentShare.query.filter_by(
                document_id=document.id,
                user_id=form.user.data
            ).first()
            
            if existing_share:
                existing_share.permission = form.permission.data
            else:
                share = DocumentShare(
                    document_id=document.id,
                    user_id=form.user.data,
                    permission=form.permission.data,
                    created_by=current_user.id
                )
                db.session.add(share)
            
            db.session.commit()
            flash('Document shared successfully.', 'success')
            return redirect(url_for('documents.share', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error sharing document: {str(e)}', 'error')
    
    shared_users = DocumentShare.query.filter_by(document_id=id).all()
    return render_template('documents/share.html',
                         document=document,
                         form=form,
                         shared_users=shared_users)

@bp.route('/<int:id>/export/<format>')
@login_required
def export(id, format):
    """Export document in various formats."""
    document = Document.query.get_or_404(id)
    
    # Check access permission
    if not document.user_can_access(current_user):
        flash('You do not have permission to access this document.', 'error')
        return redirect(url_for('documents.index'))
    
    try:
        content = get_or_create_cache(document, format)
        
        if not content:
            flash(f'Error exporting document to {format.upper()}', 'error')
            return redirect(url_for('documents.index'))
        
        # Send file
        buffer = BytesIO(content)
        filename = f"{document.title}.{format}"
        mimetype = 'application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error exporting document: {str(e)}', 'error')
        return redirect(url_for('documents.index'))

@bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """Handle bulk actions on documents."""
    form = BulkActionForm()
    
    if form.validate_on_submit():
        try:
            document_ids = [int(id) for id in form.selected_docs.data.split(',')]
            
            if form.action.data == 'categorize':
                if bulk_categorize(document_ids, form.category.data):
                    flash('Documents categorized successfully.', 'success')
                else:
                    flash('Error categorizing documents.', 'error')
                    
            elif form.action.data == 'delete':
                if bulk_delete(document_ids):
                    flash('Documents deleted successfully.', 'success')
                else:
                    flash('Error deleting documents.', 'error')
                    
            elif form.action.data == 'share':
                for doc_id in document_ids:
                    document = Document.query.get(doc_id)
                    if document and document.created_by == current_user.id:
                        share = DocumentShare(
                            document_id=doc_id,
                            user_id=form.user.data,
                            permission=form.permission.data,
                            created_by=current_user.id
                        )
                        db.session.add(share)
                db.session.commit()
                flash('Documents shared successfully.', 'success')
                
            elif form.action.data == 'export':
                # This would be handled by JavaScript to download multiple files
                pass
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error performing bulk action: {str(e)}', 'error')
    
    return redirect(url_for('documents.index'))

@bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    """Manage document categories."""
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = DocumentCategory(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully.', 'success')
            return redirect(url_for('documents.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
    
    categories = DocumentCategory.query.all()
    return render_template('documents/categories.html',
                         categories=categories,
                         form=form)

@bp.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    """Manage document tags."""
    form = TagForm()
    if form.validate_on_submit():
        try:
            tag = DocumentTag(name=form.name.data)
            db.session.add(tag)
            db.session.commit()
            flash('Tag created successfully.', 'success')
            return redirect(url_for('documents.tags'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tag: {str(e)}', 'error')
    
    tags = DocumentTag.query.all()
    return render_template('documents/tags.html',
                         tags=tags,
                         form=form)

@bp.route('/<int:id>/history')
@login_required
def history(id):
    """View document change history."""
    document = Document.query.get_or_404(id)
    
    # Check access permission
    if not document.user_can_access(current_user):
        flash('You do not have permission to access this document.', 'error')
        return redirect(url_for('documents.index'))
    
    changes = document.changes.order_by(DocumentChange.changed_at.desc()).all()
    return render_template('documents/history.html',
                         document=document,
                         changes=changes)
