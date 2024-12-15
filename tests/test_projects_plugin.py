"""Unit tests for the projects plugin."""

import unittest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app, db
from app.plugins.projects import plugin
from app.plugins.projects.models import (
    Project, Task, Todo, Comment, History,
    ProjectStatus, ProjectPriority, ValidationError
)
from app.models import User, Role

class TestProjectsPlugin(unittest.TestCase):
    """Test cases for Projects plugin."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Create test user with required roles
        self.user = User(username='test_user', email='test@example.com')
        self.user.set_password('test_password')
        self.user.roles = [
            Role(name='admin'),
            Role(name='user')
        ]
        db.session.add(self.user)
        
        # Create test status and priority
        self.status = ProjectStatus(
            name='In Progress',
            color='#ffc107',
            created_by='system'
        )
        self.priority = ProjectPriority(
            name='High',
            color='#dc3545',
            created_by='system'
        )
        db.session.add_all([self.status, self.priority])
        
        db.session.commit()
        
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def login(self):
        """Helper method to log in test user."""
        return self.client.post('/login', data={
            'username': 'test_user',
            'password': 'test_password'
        }, follow_redirects=True)
        
    def test_plugin_initialization(self):
        """Test plugin initialization and configuration."""
        self.assertEqual(plugin.metadata.name, 'projects')
        self.assertEqual(plugin.metadata.category, 'main')
        self.assertIn('admin', plugin.metadata.required_roles)
        self.assertEqual(plugin.metadata.icon, 'fa-project-diagram')
        
    def test_project_model(self):
        """Test Project model operations."""
        # Create test project
        project = Project(
            name='Test Project',
            summary='Test summary',
            description='Test description',
            status='In Progress',
            priority='High',
            created_by=self.user.username,
            lead_id=self.user.id
        )
        db.session.add(project)
        db.session.commit()
        
        # Test retrieval
        saved_project = Project.query.get(project.id)
        self.assertEqual(saved_project.name, 'Test Project')
        self.assertEqual(saved_project.status, 'In Progress')
        self.assertEqual(saved_project.lead, self.user)
        
        # Test to_dict method
        project_dict = saved_project.to_dict()
        self.assertEqual(project_dict['name'], 'Test Project')
        self.assertEqual(project_dict['status'], 'In Progress')
        self.assertEqual(project_dict['lead'], self.user.username)
        
    def test_task_model(self):
        """Test Task model operations."""
        # Create test project and task
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        task = Task(
            project_id=project.id,
            name='Test Task',
            description='Test description',
            status_id=self.status.id,
            priority_id=self.priority.id,
            created_by=self.user.username,
            assigned_to_id=self.user.id
        )
        db.session.add(task)
        db.session.commit()
        
        # Test retrieval
        saved_task = Task.query.get(task.id)
        self.assertEqual(saved_task.name, 'Test Task')
        self.assertEqual(saved_task.status.name, 'In Progress')
        self.assertEqual(saved_task.assigned_to, self.user)
        
        # Test to_dict method
        task_dict = saved_task.to_dict()
        self.assertEqual(task_dict['name'], 'Test Task')
        self.assertEqual(task_dict['status'], 'In Progress')
        self.assertEqual(task_dict['assigned_to'], self.user.username)
        
    def test_subtask_validation(self):
        """Test subtask depth validation."""
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Create task hierarchy
        task1 = Task(
            project_id=project.id,
            name='Task 1',
            created_by=self.user.username
        )
        db.session.add(task1)
        db.session.commit()
        
        task2 = Task(
            project_id=project.id,
            name='Task 2',
            parent_id=task1.id,
            created_by=self.user.username
        )
        db.session.add(task2)
        db.session.commit()
        
        task3 = Task(
            project_id=project.id,
            name='Task 3',
            parent_id=task2.id,
            created_by=self.user.username
        )
        db.session.add(task3)
        db.session.commit()
        
        # Try to create task at invalid depth
        task4 = Task(
            project_id=project.id,
            name='Task 4',
            parent_id=task3.id,
            created_by=self.user.username
        )
        
        with self.assertRaises(ValidationError):
            task4.validate_depth()
            
    def test_task_dependencies(self):
        """Test task dependency validation."""
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Create tasks
        task1 = Task(
            project_id=project.id,
            name='Task 1',
            created_by=self.user.username
        )
        task2 = Task(
            project_id=project.id,
            name='Task 2',
            created_by=self.user.username
        )
        db.session.add_all([task1, task2])
        db.session.commit()
        
        # Add dependency
        task2.dependencies.append(task1)
        db.session.commit()
        
        # Verify dependency
        self.assertIn(task1, task2.dependencies)
        self.assertIn(task2, task1.dependent_tasks)
        
        # Try to create circular dependency
        task1.dependencies.append(task2)
        
        with self.assertRaises(ValidationError):
            task1.validate_dependencies()
            
    def test_comment_system(self):
        """Test comment functionality."""
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Create comment
        comment = Comment(
            project_id=project.id,
            content='Test comment',
            created_by=self.user.username,
            user_id=self.user.id
        )
        db.session.add(comment)
        db.session.commit()
        
        # Test retrieval
        saved_comment = Comment.query.get(comment.id)
        self.assertEqual(saved_comment.content, 'Test comment')
        self.assertEqual(saved_comment.user, self.user)
        
        # Test to_dict method
        comment_dict = saved_comment.to_dict()
        self.assertEqual(comment_dict['content'], 'Test comment')
        self.assertEqual(comment_dict['user'], self.user.username)
        
    def test_history_tracking(self):
        """Test history tracking."""
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Create history entry
        history = History(
            entity_type='project',
            project_id=project.id,
            action='created',
            details={
                'name': project.name
            },
            created_by=self.user.username,
            user_id=self.user.id
        )
        db.session.add(history)
        db.session.commit()
        
        # Test retrieval
        saved_history = History.query.get(history.id)
        self.assertEqual(saved_history.action, 'created')
        self.assertEqual(saved_history.details['name'], 'Test Project')
        
        # Test to_dict method
        history_dict = saved_history.to_dict()
        self.assertEqual(history_dict['action'], 'created')
        self.assertEqual(history_dict['details']['name'], 'Test Project')
        
    def test_project_routes(self):
        """Test project management routes."""
        self.login()
        
        # Test project creation
        response = self.client.post(url_for('projects.create_project'), data={
            'name': 'New Project',
            'summary': 'Project summary',
            'description': 'Project description',
            'status': self.status.name,
            'priority': self.priority.name,
            'lead_id': self.user.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Project created successfully', response.data)
        
        project = Project.query.filter_by(name='New Project').first()
        self.assertIsNotNone(project)
        
        # Test project editing
        response = self.client.post(url_for('projects.edit_project', id=project.id), data={
            'name': 'Updated Project',
            'summary': 'Updated summary',
            'description': 'Updated description',
            'status': self.status.name,
            'priority': self.priority.name,
            'lead_id': self.user.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Project updated successfully', response.data)
        
        updated_project = Project.query.get(project.id)
        self.assertEqual(updated_project.name, 'Updated Project')
        
    def test_task_routes(self):
        """Test task management routes."""
        self.login()
        
        # Create test project
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Test task creation
        response = self.client.post(url_for('projects.create_task', project_id=project.id), data={
            'name': 'New Task',
            'description': 'Task description',
            'status_id': self.status.id,
            'priority_id': self.priority.id,
            'assigned_to_id': self.user.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task created successfully', response.data)
        
        task = Task.query.filter_by(name='New Task').first()
        self.assertIsNotNone(task)
        
        # Test task editing
        response = self.client.post(url_for('projects.edit_task', id=task.id), data={
            'name': 'Updated Task',
            'description': 'Updated description',
            'status_id': self.status.id,
            'priority_id': self.priority.id,
            'assigned_to_id': self.user.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task updated successfully', response.data)
        
        updated_task = Task.query.get(task.id)
        self.assertEqual(updated_task.name, 'Updated Task')
        
    def test_comment_routes(self):
        """Test comment management routes."""
        self.login()
        
        # Create test project
        project = Project(
            name='Test Project',
            created_by=self.user.username
        )
        db.session.add(project)
        db.session.commit()
        
        # Test comment creation
        response = self.client.post(url_for('projects.add_project_comment', project_id=project.id), data={
            'content': 'New comment'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Comment added successfully', response.data)
        
        comment = Comment.query.filter_by(content='New comment').first()
        self.assertIsNotNone(comment)
        
        # Test comment editing
        response = self.client.post(url_for('projects.edit_comment', id=comment.id), data={
            'content': 'Updated comment'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Comment updated successfully', response.data)
        
        updated_comment = Comment.query.get(comment.id)
        self.assertEqual(updated_comment.content, 'Updated comment')
        
    def test_management_routes(self):
        """Test management routes."""
        self.login()
        
        # Test status creation
        response = self.client.post(url_for('projects.create_status'), data={
            'name': 'New Status',
            'color': '#6c757d'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Status created successfully', response.data)
        
        status = ProjectStatus.query.filter_by(name='New Status').first()
        self.assertIsNotNone(status)
        
        # Test priority creation
        response = self.client.post(url_for('projects.create_priority'), data={
            'name': 'New Priority',
            'color': '#007bff'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Priority created successfully', response.data)
        
        priority = ProjectPriority.query.filter_by(name='New Priority').first()
        self.assertIsNotNone(priority)
