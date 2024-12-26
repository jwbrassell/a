from flask import render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
from flask import Blueprint
from app.models.user import User

bp = Blueprint('feature_requests', __name__, template_folder='templates')
from .models import FeatureRequest, FeatureVote, FeatureComment
import os
from werkzeug.utils import secure_filename
from datetime import datetime

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@bp.route('/list_requests')
@login_required
@requires_permission('feature_requests')
def list_requests():
    feature_requests = db.session.query(FeatureRequest)\
        .options(db.joinedload(FeatureRequest.creator))\
        .options(db.joinedload(FeatureRequest.comments).joinedload(FeatureComment.user))\
        .order_by(FeatureRequest.created_at.desc())\
        .all()
    
    # Log user data for debugging
    for request in feature_requests:
        print(f"Creator for request {request.id}: {request.creator.id}")
        print(f"Creator details - name: {request.creator.name}, username: {request.creator.username}")
        
        for comment in request.comments:
            print(f"User for comment {comment.id}: {comment.user.id}")
            print(f"User details - name: {comment.user.name}, username: {comment.user.username}")
    
    return render_template('feature_requests/list.html', 
                         feature_requests=feature_requests)

@bp.route('/submit', methods=['POST'])
@login_required
@requires_permission('feature_requests')
def submit_request():
    data = request.form.to_dict()
    
    # Handle screenshot upload
    screenshot_path = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'feature_requests', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            screenshot_path = f"feature_requests/{filename}"

    # Process impact details
    impact_details = {
        'daily_users': data.get('daily_users'),
        'time_saved': data.get('time_saved'),
        'capital_project': data.get('capital_project') == 'true',
        'capital_details': data.get('capital_details'),
        'data_source': data.get('data_source'),
        'data_contact': data.get('data_contact'),
        'data_type': data.get('data_type'),
        'workflow_needed': data.get('workflow_needed') == 'true',
        'similar_feature': data.get('similar_feature'),
        'willing_to_call': data.get('willing_to_call') == 'true'
    }

    # Get current user's full information
    user = db.session.query(User).filter_by(id=current_user.id).first()
    print(f"Creating feature request - user details - id: {user.id}, name: {user.name}, username: {user.username}")

    feature_request = FeatureRequest(
        title=data['title'],
        description=data['description'],
        page_url=data['page_url'],
        screenshot_path=screenshot_path,
        created_by=user.id,
        impact_details=impact_details
    )
    
    db.session.add(feature_request)
    db.session.commit()

    # Reload to get all relationships
    feature_request = db.session.query(FeatureRequest)\
        .options(db.joinedload(FeatureRequest.creator))\
        .filter_by(id=feature_request.id)\
        .first()
    
    return jsonify({
        'status': 'success',
        'id': feature_request.id,
        'creator_name': feature_request.creator.name or feature_request.creator.username
    })

@bp.route('/<int:request_id>/vote', methods=['POST'])
@login_required
@requires_permission('feature_requests')
def vote(request_id):
    # Get current user's full information
    user = db.session.query(User).filter_by(id=current_user.id).first()
    print(f"Processing vote - user details - id: {user.id}, name: {user.name}, username: {user.username}")

    feature_request = db.session.query(FeatureRequest)\
        .options(db.joinedload(FeatureRequest.creator))\
        .filter_by(id=request_id)\
        .first_or_404()
    
    existing_vote = FeatureVote.query.filter_by(
        feature_request_id=request_id,
        user_id=user.id
    ).first()
    
    if existing_vote:
        db.session.delete(existing_vote)
        action = 'removed'
    else:
        vote = FeatureVote(
            feature_request_id=request_id,
            user_id=user.id
        )
        db.session.add(vote)
        action = 'added'
    
    db.session.commit()
    
    vote_count = FeatureVote.query.filter_by(feature_request_id=request_id).count()
    return jsonify({
        'status': 'success',
        'action': action,
        'votes': vote_count,
        'voter_name': user.name or user.username
    })

@bp.route('/<int:request_id>/comment', methods=['POST'])
@login_required
@requires_permission('feature_requests')
def add_comment(request_id):
    feature_request = FeatureRequest.query.get_or_404(request_id)
    
    # Get current user's full information first
    user = db.session.query(User).filter_by(id=current_user.id).first()
    print(f"Adding comment - user details - id: {user.id}, name: {user.name}, username: {user.username}")
    
    comment = FeatureComment(
        feature_request_id=request_id,
        user_id=user.id,
        comment=request.form['comment']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Reload comment with user relationship
    comment = db.session.query(FeatureComment)\
        .options(db.joinedload(FeatureComment.user))\
        .filter_by(id=comment.id)\
        .first()
    
    print(f"Comment created - user details - name: {comment.user.name}, username: {comment.user.username}")
    
    # Create response data
    response_data = {
        'status': 'success',
        'comment': {
            'id': comment.id,
            'user': {
                'id': comment.user.id,
                'name': comment.user.name,  # Will be None if not set
                'username': comment.user.username  # Non-nullable
            },
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    return jsonify(response_data)

@bp.route('/admin')
@login_required
@requires_permission('feature_requests_admin')
def admin_dashboard():
    feature_requests = db.session.query(FeatureRequest)\
        .options(db.joinedload(FeatureRequest.creator))\
        .options(db.joinedload(FeatureRequest.comments).joinedload(FeatureComment.user))\
        .order_by(FeatureRequest.created_at.desc())\
        .all()
    
    # Log user data for debugging
    for request in feature_requests:
        print(f"Creator for request {request.id}: {request.creator.id}")
        print(f"Creator details - name: {request.creator.name}, username: {request.creator.username}")
        
        for comment in request.comments:
            print(f"User for comment {comment.id}: {comment.user.id}")
            print(f"User details - name: {comment.user.name}, username: {comment.user.username}")
    
    return render_template('feature_requests/admin_dashboard.html', 
                         feature_requests=feature_requests)

@bp.route('/<int:request_id>/status', methods=['POST'])
@login_required
@requires_permission('feature_requests_admin')
def update_status(request_id):
    # Get current user's full information
    user = db.session.query(User).filter_by(id=current_user.id).first()
    print(f"Updating status - admin user details - id: {user.id}, name: {user.name}, username: {user.username}")

    feature_request = db.session.query(FeatureRequest)\
        .options(db.joinedload(FeatureRequest.creator))\
        .filter_by(id=request_id)\
        .first_or_404()
    
    old_status = feature_request.status
    feature_request.status = request.form['status']
    db.session.commit()
    
    print(f"Status updated from {old_status} to {feature_request.status} by {user.name or user.username}")
    
    return jsonify({
        'status': 'success',
        'feature_request': {
            'id': feature_request.id,
            'title': feature_request.title,
            'new_status': feature_request.status,
            'updated_by': user.name or user.username
        }
    })
