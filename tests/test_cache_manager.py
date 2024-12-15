import unittest
import time
from datetime import datetime
from flask import Flask, Response
from app.utils.cache_manager import CacheManager, cached, memoize, cache_response

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config.update({
            'TESTING': True,
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300
        })
        
        self.cache_manager = CacheManager(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up test environment."""
        self.cache_manager.clear_all()
        self.app_context.pop()

    def test_basic_caching(self):
        """Test basic caching functionality."""
        test_key = 'test_key'
        test_value = 'test_value'
        
        # Set value in cache
        self.cache_manager.memory_cache.set(test_key, test_value)
        
        # Get value from cache
        cached_value = self.cache_manager.memory_cache.get(test_key)
        self.assertEqual(cached_value, test_value)

    def test_multi_level_caching(self):
        """Test multi-level caching decorator."""
        call_count = 0
        
        @self.cache_manager.cached(timeout=1)
        def test_function():
            nonlocal call_count
            call_count += 1
            return f'result_{call_count}'
        
        # First call - should hit the function
        result1 = test_function()
        self.assertEqual(result1, 'result_1')
        self.assertEqual(call_count, 1)
        
        # Second call - should hit the cache
        result2 = test_function()
        self.assertEqual(result2, 'result_1')
        self.assertEqual(call_count, 1)
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Third call - should hit the function again
        result3 = test_function()
        self.assertEqual(result3, 'result_2')
        self.assertEqual(call_count, 2)

    def test_memoization(self):
        """Test memoization decorator."""
        class TestClass:
            def __init__(self):
                self.call_count = 0
            
            @memoize(timeout=1)
            def test_method(self, arg):
                self.call_count += 1
                return f'result_{arg}_{self.call_count}'
        
        test_instance = TestClass()
        
        # First call
        result1 = test_instance.test_method('test')
        self.assertEqual(result1, 'result_test_1')
        self.assertEqual(test_instance.call_count, 1)
        
        # Second call with same argument - should hit cache
        result2 = test_instance.test_method('test')
        self.assertEqual(result2, 'result_test_1')
        self.assertEqual(test_instance.call_count, 1)
        
        # Call with different argument
        result3 = test_instance.test_method('other')
        self.assertEqual(result3, 'result_other_2')
        self.assertEqual(test_instance.call_count, 2)

    def test_response_caching(self):
        """Test response caching decorator."""
        @self.app.route('/test')
        @self.cache_manager.cache_response(timeout=1)
        def test_view():
            return Response('test response', status=200)
        
        with self.app.test_client() as client:
            # First request
            response1 = client.get('/test')
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response1.data.decode(), 'test response')
            
            # Second request - should hit cache
            response2 = client.get('/test')
            self.assertEqual(response2.status_code, 200)
            self.assertEqual(response2.data.decode(), 'test response')
            
            # POST request - should not be cached
            response3 = client.post('/test')
            self.assertEqual(response3.status_code, 405)  # Method not allowed

    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = self.cache_manager.generate_cache_key('arg1', 'arg2', kwarg1='val1')
        key2 = self.cache_manager.generate_cache_key('arg1', 'arg2', kwarg1='val1')
        key3 = self.cache_manager.generate_cache_key('arg1', 'arg2', kwarg1='val2')
        
        # Same arguments should generate same key
        self.assertEqual(key1, key2)
        
        # Different arguments should generate different keys
        self.assertNotEqual(key1, key3)

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        @self.app.route('/metrics-test')
        def test_view():
            time.sleep(0.1)  # Simulate some work
            return 'test'
        
        with self.app.test_client() as client:
            # Make some requests
            for _ in range(3):
                client.get('/metrics-test')
            
            # Get metrics
            metrics = self.cache_manager.get_performance_metrics('metrics-test')
            
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics['count'], 3)
            self.assertGreater(metrics['avg_duration'], 0)
            self.assertLess(metrics['min_duration'], metrics['max_duration'])

    def test_cache_stats(self):
        """Test cache statistics collection."""
        # Make some cache operations
        self.cache_manager.memory_cache.set('key1', 'value1')
        self.cache_manager.memory_cache.set('key2', 'value2')
        self.cache_manager.memory_cache.get('key1')
        self.cache_manager.memory_cache.get('nonexistent')
        
        stats = self.cache_manager.get_cache_stats()
        
        self.assertIn('memory_cache', stats)
        self.assertIn('filesystem_cache', stats)
        self.assertEqual(stats['memory_cache']['size'], 2)

    def test_cache_warming(self):
        """Test cache warming functionality."""
        # This is a basic test since actual warming depends on your models
        self.cache_manager.warm_cache()
        
        # Verify that warming didn't raise any exceptions
        # In a real application, you'd verify specific cached data

    def test_clear_pattern(self):
        """Test clearing cache by pattern."""
        # Set some test values
        self.cache_manager.memory_cache.set('test:1', 'value1')
        self.cache_manager.memory_cache.set('test:2', 'value2')
        self.cache_manager.memory_cache.set('other:1', 'value3')
        
        # Clear test pattern
        self.cache_manager.clear_pattern('test:*')
        
        # Verify clearing worked
        self.assertIsNone(self.cache_manager.memory_cache.get('test:1'))
        self.assertIsNone(self.cache_manager.memory_cache.get('test:2'))
        self.assertIsNotNone(self.cache_manager.memory_cache.get('other:1'))

if __name__ == '__main__':
    unittest.main()
