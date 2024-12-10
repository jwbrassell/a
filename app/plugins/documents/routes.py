from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.plugins.documents import bp
from app.plugins.documents.models import Document, DocumentCategory, DocumentTag, DocumentChange
from app.plugins.documents.forms import DocumentForm, CategoryForm, TagForm

@bp.route('/')
@login_required
def index():
    """Display main documents page."""
    documents = Document.query.order_by(Document.updated_at.desc()).all()
    categories = DocumentCategory.query.all()
    return render_template('documents/index.html',
                         documents=documents,
                         categories=categories)

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
                db.session.flush()  # Get the ID without committing
                category_id = new_category.id
            
            # Create document
            document = Document(
                title=form.title.data,
                content=form.content.data,
                category_id=category_id,
                created_by=current_user.id
            )
            db.session.add(document)
            
            # Handle existing tags
            if form.tags.data:
                selected_tags = DocumentTag.query.filter(DocumentTag.id.in_(form.tags.data)).all()
                document.tags.extend(selected_tags)
            
            # Handle new tags if provided
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

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing document."""
    document = Document.query.get_or_404(id)
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
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    
    documents = Document.query
    
    if query:
        documents = documents.filter(
            or_(
                Document.title.ilike(f'%{query}%'),
                Document.content.ilike(f'%{query}%')
            )
        )
    
    if category_id:
        documents = documents.filter_by(category_id=category_id)
    
    if tag_id:
        documents = documents.filter(Document.tags.any(id=tag_id))
    
    documents = documents.order_by(Document.updated_at.desc()).all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([doc.to_dict() for doc in documents])
    
    categories = DocumentCategory.query.all()
    tags = DocumentTag.query.all()
    return render_template('documents/search.html',
                         documents=documents,
                         categories=categories,
                         tags=tags,
                         query=query,
                         selected_category=category_id,
                         selected_tag=tag_id)

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
    changes = document.changes.order_by(DocumentChange.changed_at.desc()).all()
    return render_template('documents/history.html',
                         document=document,
                         changes=changes)
