from flask import render_template, jsonify, request, current_app
from . import example
from .models import ExampleData
from app.extensions import db, csrf
from sqlalchemy.exc import SQLAlchemyError

@example.route('/')
def index():
    return render_template('example/index.html')

@example.route('/data', methods=['GET'])
def get_data():
    try:
        data = ExampleData.query.all()
        return jsonify([item.to_dict() for item in data])
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@example.route('/data', methods=['POST'])
@csrf.exempt  # Since we're handling CSRF via X-CSRFToken header
def add_data():
    try:
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            value = float(data['value'])
        except (TypeError, ValueError):
            return jsonify({'error': 'Value must be a number'}), 400

        new_entry = ExampleData(
            key=str(data['key']),
            value=value
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify(new_entry.to_dict()), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in add_data: {str(e)}")
        return jsonify({'error': 'Failed to save data'}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in add_data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
