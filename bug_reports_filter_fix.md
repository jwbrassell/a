# Bug Reports Filter Issue Analysis & Fix Plan

## Current Behavior
1. Click status filter "not actionable"
2. Click apply filter
3. Loading spinner appears and stays
4. DataTable doesn't update
5. No console errors

## Potential Issues

### 1. Frontend (DataTables Configuration)
- DataTables might not be properly configured for server-side processing
- AJAX request format might not match what the server expects
- Filter data might not be properly formatted in the AJAX request
- Loading state management might be interfering with DataTables' internal state

### 2. Backend (Flask Route)
- `/bug_reports/admin/data` endpoint might not be properly handling DataTables server-side parameters
- Response format might not match what DataTables expects
- Filter parameters might not be properly extracted from request
- SQL query might be incorrect or timing out

## Investigation Steps

1. **Verify Route Registration**
   - Confirm `/bug_reports/admin/data` route is properly registered
   - Check URL prefix handling
   - Add logging to verify route is being hit

2. **Verify AJAX Request**
   - Add console.log to print out AJAX request data
   - Verify filter values are being properly included
   - Check network tab for request format

3. **Verify Server Processing**
   - Add detailed logging for incoming requests
   - Log filter parameters being received
   - Log SQL query being generated
   - Log response data before sending

## Implementation Plan

1. **Frontend Updates**
```javascript
// Debug AJAX request
ajax: {
    url: '/bug_reports/admin/data',
    type: 'GET',
    data: function(d) {
        console.log('DataTables request:', d);  // Debug
        const filters = {
            status: $('#statusFilter').val(),
            type: $('#typeFilter').val(),
            route: $('#routeFilter').val(),
            date: $('#dateFilter').val()
        };
        console.log('Custom filters:', filters);  // Debug
        return {...d, ...filters};
    }
}
```

2. **Backend Updates**
```python
@bp.route('/admin/data')
@login_required
@requires_permission('bug_reports_admin')
def admin_data():
    # Debug logging
    current_app.logger.info(f"Received DataTables request: {request.args}")
    
    try:
        # Extract DataTables parameters with defaults
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=25)
        
        # Log filter parameters
        current_app.logger.info(f"Filters - Status: {request.args.get('status')}, "
                              f"Type: {request.args.get('type')}, "
                              f"Route: {request.args.get('route')}")
        
        # Build query with debug logging
        query = BugReport.query
        if request.args.get('status'):
            query = query.filter(BugReport.status == request.args.get('status'))
            current_app.logger.info(f"Applied status filter: {request.args.get('status')}")
        
        # Log final query
        current_app.logger.info(f"Final query: {query}")
        
        # Execute query with error handling
        try:
            data = query.offset(start).limit(length).all()
            total_records = query.count()
        except Exception as e:
            current_app.logger.error(f"Query execution error: {str(e)}")
            raise
        
        # Log response
        response_data = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': [report.to_dict() for report in data]
        }
        current_app.logger.info(f"Sending response: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in admin_data: {str(e)}")
        return jsonify({
            'error': str(e),
            'draw': request.args.get('draw', type=int),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        }), 500
```

## Testing Steps

1. **Frontend Testing**
   - Check browser console for AJAX request logging
   - Verify filter values in network request
   - Confirm DataTables is receiving proper response format

2. **Backend Testing**
   - Check Flask logs for request handling
   - Verify filter parameters are received
   - Confirm SQL query is correct
   - Validate response format

3. **Integration Testing**
   - Test each filter type individually
   - Test multiple filters together
   - Verify loading state behavior
   - Check table updates correctly

## Success Criteria
1. Loading spinner appears when filters applied
2. AJAX request contains correct filter parameters
3. Server processes request and returns filtered data
4. Loading spinner disappears after data loaded
5. Table updates with filtered data
6. No UI freezing during process

## Implementation Order
1. Add detailed logging
2. Update backend route with proper error handling
3. Fix frontend DataTables configuration
4. Test and verify each step
5. Clean up debugging code once fixed
