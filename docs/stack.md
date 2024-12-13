# Portal Technology Stack & Capabilities

## Core Technology Stack

### Backend Framework
- **Python 3.x**
- **Flask** - Web framework with extensive plugin architecture
- **SQLAlchemy** - ORM for database interactions
- **Alembic** - Database migration tool
- **Gunicorn** - WSGI HTTP Server for production deployment

### Database Support
- **MariaDB/MySQL** (via PyMySQL)
- **SQLite** (fallback/development)
- Configurable database connection pooling with optimized settings:
  - Pool size: 30
  - Pool recycle: 3600s
  - Connection timeout: 20s
  - LIFO pool usage for reduced thread contention

### Caching System
- **Flask-Caching** with SimpleCache backend
- **Multi-level caching strategy:**
  - Default cache timeout: 300s (5 minutes)
  - Project stats cache: 60s
  - Granular cache decorators for:
    - Project data
    - Task data
    - Project statistics
    - User project lists
    - Project team data
- **Cache management features:**
  - Automatic cache invalidation
  - Cache warming capabilities
  - Project-specific cache management
  - Task-specific cache management
  - User-related cache management

### Session Management
- **Flask-Session** with SQLAlchemy backend
  - Session lifetime: 2 hours
  - Signed sessions
  - SQL-based session storage

### Frontend Assets
- Static file serving with optimized cache policies:
  - Fonts: 1 year cache
  - Images: 30 days cache
  - General static files: 30 days cache
- ETag support for all static files
- Content delivery optimization through cache control headers

## Security Features

### Authentication & Authorization
- **Flask-Login** for user authentication
- **Role-Based Access Control (RBAC)**
  - Fine-grained route access control
  - Role-based permission system
  - Admin override capabilities
  - Dynamic route access mapping
  - Automatic route validation
  - Role hierarchy support

### Security Headers & Protections
- **CSRF Protection** via Flask-WTF
- **Content Security Policy (CSP)**
  - Strict resource loading policies
  - XSS protection
  - Frame protection
- **Additional Security Headers**
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: SAMEORIGIN
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
  - HSTS (in production)

### Data Protection
- **Bcrypt** password hashing
- **PyMySQL** with UTF-8 encoding
- **HTTPS enforcement** in production
- **Signed session cookies**

## Activity Tracking & Monitoring

### User Activity Tracking
- Automatic route access tracking
- User action logging
- Activity history maintenance
- Error resilient tracking system
- Per-user activity monitoring

### System Monitoring
- Route access patterns
- User engagement metrics
- Error tracking and logging
- Performance monitoring

## Plugin Architecture

### Available Plugins
1. **Admin Plugin**
   - Route management
   - Administrative controls
   
2. **Documents Plugin**
   - Document management system
   - File handling capabilities

3. **Projects Plugin**
   - Project management
   - Task tracking
   - Priority and status management
   - Team collaboration features
   - Project statistics
   - Cache-optimized data access

4. **Reports Plugin**
   - Custom report generation
   - Dashboard views
   - Data visualization

5. **Profile Plugin**
   - User profile management
   - User preferences

6. **Tracking Plugin**
   - Activity monitoring
   - Usage analytics

7. **Handoffs Plugin**
   - Workflow management
   - Task handoff system

8. **OnCall Plugin**
   - On-call schedule management
   - Rotation tracking

9. **Weblinks Plugin**
   - Link management
   - Resource organization

10. **Dispatch Plugin**
    - Task dispatching
    - Work distribution

### Plugin Features
- Modular architecture
- Independent routing
- Dedicated templates
- Plugin-specific models
- Isolated configurations
- Plugin-specific caching strategies

## Development Features

### Environment Management
- **python-dotenv** for environment configuration
- Development/Testing/Production configurations
- Environment-specific logging levels

### Logging & Monitoring
- Configurable logging levels
- Syslog integration in production
- Activity tracking
- Performance monitoring
- Error tracking

### Development Tools
- Database migration support
- Route management utilities
- RBAC management tools
- Cache management utilities
- Activity tracking decorators

## Performance Optimizations

### Database
- Connection pooling
- Pool recycling
- Pre-ping enabled
- Optimized pool timeout

### Caching
- SimpleCache-based caching system
- Multi-level cache strategy
- Automatic cache invalidation
- Cache warming capabilities
- Granular cache timeouts
- Cache decorators for common operations

### Security Performance
- Efficient RBAC checks
- Optimized session handling
- Fast password hashing
- Quick route validation

## Deployment Capabilities

### Server Configuration
- Gunicorn WSGI server
- Configurable worker processes
- Graceful timeout handling
- Static file serving

### Monitoring & Maintenance
- Activity tracking
- Route cleanup utilities
- Invalid mapping detection
- Session management tools
- Cache management system

### Scalability Features
- In-memory caching support
- Database connection pooling
- Modular plugin architecture
- Configurable worker processes
- Efficient cache invalidation
