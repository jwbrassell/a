# Redis Integration Guide for Flask Applications

This guide explains how to integrate Redis with your Flask application for caching, session management, and other data storage needs.

## Redis vs. Pinecone: Choosing the Right Tool

While both Redis and Pinecone are database technologies, they serve different purposes:

### Redis
- **Primary Use Cases**:
  - In-memory caching
  - Session management
  - Real-time analytics
  - Queue management
  - Rate limiting
  - Simple key-value storage
- **Strengths**:
  - Extremely fast (in-memory)
  - Versatile data structures
  - Built-in persistence
  - Great for temporary data storage
  - Excellent for caching
  - Low latency
  - Simple to set up and use

### Pinecone
- **Primary Use Cases**:
  - Vector similarity search
  - Machine learning feature storage
  - Semantic search
  - Recommendation systems
  - AI/ML applications
- **Strengths**:
  - Specialized for vector embeddings
  - Optimized for similarity search
  - Scales well for ML workloads
  - Maintains high performance with large vector datasets
  - Built-in support for vector operations

### When to Choose Which:

Choose **Redis** when you need:
- Fast caching layer
- Session management
- Simple key-value storage
- Rate limiting
- Real-time analytics
- Queue management
- Temporary data storage

Choose **Pinecone** when you need:
- Vector similarity search
- AI/ML feature storage
- Semantic search capabilities
- Large-scale vector operations
- Recommendation engines based on embeddings
- Complex similarity-based queries

For most traditional web applications, Redis is the better choice due to its versatility and simpler implementation. Pinecone is more specialized and should be chosen when you specifically need vector search capabilities or are building AI/ML-focused applications.

## Installation Requirements

Add these packages to your `requirements.txt`:

```
redis==5.0.1
Flask-Redis==0.4.0
```

## Basic Setup

### 1. Configure Redis in config.py

Add Redis configuration to your `config.py`:

```python
class Config:
    # ... other config settings ...
    
    # Redis Configuration
    REDIS_URL = "redis://localhost:6379/0"  # Default Redis URL
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None  # Set this if your Redis server requires authentication
```

### 2. Initialize Redis in extensions.py

In your `app/extensions.py`, add Redis initialization:

```python
from flask_redis import FlaskRedis

redis_client = FlaskRedis()
```

### 3. Setup Redis in Factory Pattern

In your application factory (`app/__init__.py`), initialize Redis:

```python
from .extensions import redis_client

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Redis
    redis_client.init_app(app)
    
    # ... rest of your initialization code ...
    return app
```

## Usage Examples

### Basic Key-Value Operations

```python
from app.extensions import redis_client

# Set a value
redis_client.set('my_key', 'my_value')

# Get a value
value = redis_client.get('my_key')

# Set with expiration (in seconds)
redis_client.setex('temp_key', 3600, 'expires in 1 hour')

# Delete a key
redis_client.delete('my_key')
```

### Caching Example

```python
from functools import wraps
import json

def redis_cached(timeout=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(kwargs)
            
            # Try to get the cached value
            result = redis_client.get(cache_key)
            if result is not None:
                return json.loads(result)
            
            # If not cached, execute the function
            result = f(*args, **kwargs)
            
            # Cache the result
            redis_client.setex(cache_key, timeout, json.dumps(result))
            return result
        return decorated_function
    return decorator

# Usage example:
@redis_cached(timeout=3600)
def get_user_data(user_id):
    # Expensive database query or API call
    return {"user_id": user_id, "data": "some data"}
```

### Session Storage

```python
from datetime import timedelta
from flask import session

# In your app config
app.config.update(
    SESSION_TYPE='redis',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# Usage in routes
@app.route('/set_session')
def set_session():
    session['user_id'] = 123
    return 'Session value set'

@app.route('/get_session')
def get_session():
    user_id = session.get('user_id')
    return f'User ID: {user_id}'
```

### Rate Limiting Example

```python
def rate_limit(key_prefix, limit=100, period=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"{key_prefix}:{request.remote_addr}"
            current = redis_client.get(key)
            
            if current is None:
                redis_client.setex(key, period, 1)
            elif int(current) >= limit:
                abort(429)  # Too Many Requests
            else:
                redis_client.incr(key)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage example:
@app.route('/api/endpoint')
@rate_limit('api_calls', limit=100, period=3600)
def api_endpoint():
    return jsonify({"message": "API response"})
```

## Best Practices

1. **Connection Management**: Redis connections are managed automatically by Flask-Redis.

2. **Error Handling**: Always implement proper error handling:
```python
from redis.exceptions import RedisError

try:
    redis_client.set('key', 'value')
except RedisError as e:
    # Handle Redis errors appropriately
    app.logger.error(f"Redis error: {e}")
```

3. **Environment Variables**: Use environment variables for Redis configuration:
```python
class Config:
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

4. **Health Checks**: Implement Redis health checks:
```python
def check_redis_health():
    try:
        redis_client.ping()
        return True
    except RedisError:
        return False
```

## Production Considerations

1. **Security**:
   - Use strong passwords
   - Configure Redis to only listen on localhost
   - Use SSL/TLS for remote connections
   - Implement proper firewall rules

2. **Performance**:
   - Monitor Redis memory usage
   - Implement key expiration policies
   - Use appropriate data structures
   - Consider Redis persistence options

3. **High Availability**:
   - Consider Redis Sentinel for high availability
   - Implement proper backup strategies
   - Use Redis Cluster for scaling

## Troubleshooting

Common issues and solutions:

1. **Connection Refused**:
   - Check if Redis server is running
   - Verify correct host/port configuration
   - Check firewall settings

2. **Authentication Failed**:
   - Verify Redis password configuration
   - Check if authentication is enabled on Redis server

3. **Memory Issues**:
   - Monitor Redis memory usage
   - Implement proper key expiration
   - Consider Redis maxmemory configuration

## Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Flask-Redis Documentation](https://github.com/underyx/flask-redis)
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [Pinecone Documentation](https://docs.pinecone.io/) (for vector search alternatives)
