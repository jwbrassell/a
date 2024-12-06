[Previous content until API Endpoints section, which I'll enhance...]

## API Endpoints

### Document Management

#### List Documents
```python
@bp.route('/')
@login_required
def index():
    """Display main documents page."""
    documents = Document.query.order_by(Document.updated_at.desc()).all()
    categories = DocumentCategory.query.all()
    return render_template('documents/index.html',
                         documents=documents,
                         categories=categories)
```
- Method: GET
- URL: /documents/
- Authentication: Required
- Response: Rendered template with documents sorted by last update

#### Create Document
```python
@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new document."""
    # GET: Display creation form
    # POST: Handle document creation
```
Features:
- Dynamic category and tag choices population
- New category creation support
- Comma-separated new tags support
- Transaction management
- Change history recording
- Error handling with rollback

Workflow:
1. Form validation
2. Handle new category if provided
3. Create document
4. Process existing tags
5. Process new tags
6. Record change history
7. Commit transaction

#### Edit Document
```python
@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing document."""
    # GET: Display edit form with populated data
    # POST: Handle document update
```
Features:
- Pre-populated form data
- Previous version preservation
- Tag management (add/remove)
- Category management
- Transaction safety
- Change history tracking

Workflow:
1. Load existing document
2. Validate form submission
3. Store previous content
4. Update document properties
5. Handle tag changes
6. Record change history
7. Commit transaction

### Search Functionality

#### Search Documents
```python
@bp.route('/search')
@login_required
def search():
    """Search documents with multiple criteria."""
    # Build query based on filters
    documents = Document.query
    
    # Apply text search
    if query:
        documents = documents.filter(
            or_(
                Document.title.ilike(f'%{query}%'),
                Document.content.ilike(f'%{query}%')
            )
        )
    
    # Apply category filter
    if category_id:
        documents = documents.filter_by(category_id=category_id)
    
    # Apply tag filter
    if tag_id:
        documents = documents.filter(Document.tags.any(id=tag_id))
```
Features:
- Multiple search criteria support
- AJAX support for dynamic results
- JSON response for AJAX requests
- Template rendering for direct access
- Combined filters (text + category + tag)

AJAX Response Format:
```python
{
    'id': document.id,
    'title': document.title,
    'category': document.category.name,
    'tags': [tag.name for tag in document.tags],
    'created_by': document.creator.username,
    'created_at': formatted_datetime,
    'updated_at': formatted_datetime
}
```

### Category Management

#### Manage Categories
```python
@bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    """Manage document categories."""
    # GET: Display categories and creation form
    # POST: Handle category creation
```
Features:
- Category creation form
- Unique name validation
- Error handling
- Transaction management
- Category listing with document counts

### Tag Management

#### Manage Tags
```python
@bp.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    """Manage document tags."""
    # GET: Display tags and creation form
    # POST: Handle tag creation
```
Features:
- Tag creation form
- Usage statistics
- Tag cloud visualization
- Error handling
- Transaction management

### Version History

#### View History
```python
@bp.route('/<int:id>/history')
@login_required
def history(id):
    """View document change history."""
    document = Document.query.get_or_404(id)
    changes = document.changes.order_by(DocumentChange.changed_at.desc()).all()
```
Features:
- Chronological change listing
- Previous version preservation
- Change type indication
- User attribution
- Timeline visualization

### Error Handling

All routes implement comprehensive error handling:
```python
try:
    # Operation logic
    db.session.commit()
    flash('Success message', 'success')
except Exception as e:
    db.session.rollback()
    flash(f'Error message: {str(e)}', 'error')
```

### Transaction Management

Critical operations are wrapped in transactions:
1. Begin transaction (implicit with db.session)
2. Perform operations
3. Use db.session.flush() for ID generation
4. Commit on success
5. Rollback on error
