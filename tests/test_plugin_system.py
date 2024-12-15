import unittest
from pathlib import Path
import tempfile
import shutil
from flask import Flask
from werkzeug.security import generate_password_hash
from app.utils.plugin_base import PluginBase, PluginMetadata, PluginError
from app.utils.plugin_manager import PluginManager
from app.extensions import db
from app.models.user import User
from app.models.role import Role

class TestPluginSystem(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-key',
            'PLUGIN_ENABLED': True,
            'PLUGIN_AUTO_LOAD': False
        })
        
        # Initialize extensions
        db.init_app(self.app)
        
        # Create temporary plugin directory
        self.temp_dir = tempfile.mkdtemp()
        self.app.config['PLUGIN_DIR'] = self.temp_dir
        
        # Create application context
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Create database tables
        db.create_all()
        
        # Create test user and role
        self.create_test_user()

    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        shutil.rmtree(self.temp_dir)

    def create_test_user(self):
        """Create test user and role."""
        role = Role(name='admin')
        db.session.add(role)
        
        user = User(
            username='test_user',
            email='test@example.com',
            password_hash=generate_password_hash('password'),
            roles=[role]
        )
        db.session.add(user)
        db.session.commit()

    def create_test_plugin(self):
        """Create a test plugin class."""
        class TestPlugin(PluginBase):
            def __init__(self):
                metadata = PluginMetadata(
                    name='test_plugin',
                    version='1.0.0',
                    description='Test plugin',
                    author='Test Author',
                    required_roles=['admin'],
                    icon='fas fa-test',
                    category='test',
                    weight=100
                )
                super().__init__(metadata)
                self.init_blueprint()
            
            def register_routes(self):
                @self.blueprint.route('/')
                def index():
                    return 'Test Plugin Index'
        
        return TestPlugin

    def test_plugin_base(self):
        """Test PluginBase functionality."""
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Test metadata
        self.assertEqual(plugin.metadata.name, 'test_plugin')
        self.assertEqual(plugin.metadata.version, '1.0.0')
        
        # Test blueprint initialization
        self.assertIsNotNone(plugin.blueprint)
        self.assertEqual(plugin.blueprint.name, 'test_plugin')
        
        # Test URL prefix
        self.assertEqual(plugin.blueprint.url_prefix, '/test_plugin')

    def test_plugin_manager(self):
        """Test PluginManager functionality."""
        manager = PluginManager(self.app)
        
        # Test plugin loading
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Register plugin with manager
        manager.plugins['test_plugin'] = plugin
        
        # Test plugin retrieval
        loaded_plugin = manager.get_plugin('test_plugin')
        self.assertIsNotNone(loaded_plugin)
        self.assertEqual(loaded_plugin.metadata.name, 'test_plugin')
        
        # Test plugin unloading
        success = manager.unload_plugin('test_plugin')
        self.assertTrue(success)
        self.assertNotIn('test_plugin', manager.plugins)

    def test_plugin_error_handling(self):
        """Test plugin error handling."""
        # Test invalid metadata
        with self.assertRaises(PluginError):
            class InvalidPlugin(PluginBase):
                def __init__(self):
                    metadata = PluginMetadata(
                        name='',  # Invalid empty name
                        version='1.0.0',
                        description='Test plugin',
                        author='Test Author',
                        required_roles=['admin'],
                        icon='fas fa-test',
                        category='test',
                        weight=100
                    )
                    super().__init__(metadata)

    def test_plugin_template_handling(self):
        """Test plugin template handling."""
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Test template path generation
        template_path = plugin.get_template_path('index.html')
        self.assertEqual(template_path, 'test_plugin/index.html')

    def test_plugin_static_files(self):
        """Test plugin static file handling."""
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Test static URL generation
        static_url = plugin.register_static_resource('test.css')
        self.assertEqual(static_url, '/test_plugin/static/test.css')

    def test_plugin_logging(self):
        """Test plugin logging functionality."""
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Test action logging
        plugin.log_action('test_action', {'detail': 'test'})
        # Note: In a real test, you'd verify the log output

    def test_plugin_configuration(self):
        """Test plugin configuration handling."""
        TestPlugin = self.create_test_plugin()
        plugin = TestPlugin()
        
        # Test plugin enabled status
        self.assertTrue(plugin.is_enabled)
        
        # Test plugin config
        self.assertEqual(plugin.config, {})
        
        # Test with custom config
        self.app.config['PLUGIN_TEST_PLUGIN_CONFIG'] = {'setting': 'value'}
        self.assertEqual(plugin.config, {'setting': 'value'})

    def test_plugin_dependencies(self):
        """Test plugin dependency validation."""
        manager = PluginManager(self.app)
        
        # Create plugins with dependencies
        class PluginA(PluginBase):
            def __init__(self):
                metadata = PluginMetadata(
                    name='plugin_a',
                    version='1.0.0',
                    description='Plugin A',
                    author='Test Author',
                    required_roles=['admin'],
                    icon='fas fa-test',
                    category='test',
                    weight=100
                )
                super().__init__(metadata)
        
        class PluginB(PluginBase):
            def __init__(self):
                metadata = PluginMetadata(
                    name='plugin_b',
                    version='1.0.0',
                    description='Plugin B',
                    author='Test Author',
                    required_roles=['admin'],
                    icon='fas fa-test',
                    category='test',
                    weight=100
                )
                metadata.required_plugins = ['plugin_a']
                super().__init__(metadata)
        
        # Register plugins
        manager.plugins['plugin_a'] = PluginA()
        manager.plugins['plugin_b'] = PluginB()
        
        # Test dependency validation
        self.assertTrue(manager.validate_plugin_dependencies('plugin_a'))
        self.assertTrue(manager.validate_plugin_dependencies('plugin_b'))
        
        # Test with missing dependency
        manager.plugins.pop('plugin_a')
        self.assertFalse(manager.validate_plugin_dependencies('plugin_b'))

if __name__ == '__main__':
    unittest.main()
