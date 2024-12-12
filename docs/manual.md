# Black Friday Lunch Application Manual

[Previous content remains exactly the same until after the Caching System section]

### DataTables Server-Side Processing

The application uses server-side processing for large datasets to improve performance and reduce initial page load times. Here are the key implementations:

#### 1. Client-Side Implementation
```javascript
// Example DataTable initialization with server-side processing
$('#data-table').DataTable({
    "processing": true,
    "serverSide": true,
    "ajax": "/api/data",
    "columns": [
        { "data": "id" },
        { "data": "name" },
        { "data": "status" },
        { "data": "created" }
    ],
    "language": {
        "processing": '<i class="fa fa-spinner fa-spin"></i> Loading...'
    }
});
```

#### 2. Server-Side Implementation Pattern
```python
@bp.route('/api/data')
@login_required
def get_data():
    # Get DataTables parameters
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', type=int, default=0)
    length = request.args.get('length', type=int, default=10)
    search = request.args.get('search[value]', type=str, default='')
    
    # Base query
    query = Model.query
    
    # Apply search if provided
    if search:
        query = query.filter(or_(
            Model.field1.ilike(f'%{search}%'),
            Model.field2.ilike(f'%{search}%')
        ))
    
    # Get total records before filtering
    total = query.count()
    
    # Apply pagination
    records = query.order_by(Model.created_at.desc())\
                  .offset(start)\
                  .limit(length)\
                  .all()
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': [record.to_dict() for record in records]
    })
```

#### 3. Best Practices

1. **Enable Processing Indicator**
   - Show loading state during AJAX requests
   - Customize the loading message/spinner

2. **Optimize Column Definitions**
   - Disable sorting/searching for columns that don't need it
   - Use proper data types for sorting

3. **Handle Large Datasets**
   - Always use server-side processing for tables with more than 100 records
   - Implement proper indexing on searched/sorted columns

4. **Error Handling**
   - Implement proper error handling in AJAX callbacks
   - Show user-friendly error messages

5. **Performance Tips**
   - Cache results when possible
   - Use database indexes effectively
   - Optimize queries for pagination

[Rest of the manual content remains exactly the same]
