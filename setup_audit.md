# Setup Scripts Audit

## Core Requirements
- Flask DB initialization
- Flask DB migrations
- Gunicorn deployment

## Files Analysis

### Essential Files (Keep)
1. `wsgi.py` - Required for Gunicorn
2. `config.py` - Core configuration
3. `migrations_config.py` - Required for database migrations
4. `app/` - Core application directory
5. `requirements.txt` - Dependencies
6. `.env` and `.env.example` - Environment configuration
7. `gunicorn.conf.py` - Gunicorn configuration

### Setup Scripts to Remove
1. `setup_app.py` - No longer needed as environment setup is handled by new repo
2. `setup_dispatch.py` - Dispatch setup can be handled by migrations
3. `setup_handoffs.py` - Handoffs setup can be handled by migrations
4. `init_actions.py` - Actions can be handled by migrations
5. `init_database.py` - Replaced by `flask db init/upgrade`
6. `package_init_db.py` - No longer needed
7. `temp_init.py` - Temporary file that can be removed
8. `oncall_init.py` - OnCall setup can be handled by migrations

### Vault-Related Files to Remove
1. `vault_utility.py` - Vault setup handled by new repo
2. `scripts/setup_secure_vault.py` - Vault setup handled by new repo
3. `scripts/reinit_vault_policies.py` - Vault policies handled by new repo
4. `scripts/vault_manage.ps1` - Vault management handled by new repo
5. `scripts/vault_manage.sh` - Vault management handled by new repo
6. `config/vault-*.hcl*` - Vault configuration handled by new repo
7. `config/vault.service` - Vault service handled by new repo

### Service Files to Remove
1. `flask_app.service` - Service configuration handled by new repo

## New Simplified Setup Process

1. Database Initialization:
```bash
flask db init
flask db upgrade
```

2. Application Deployment:
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

## Migration Notes

1. Ensure all necessary database migrations are in place before removing initialization scripts
2. Any custom data seeding should be moved to migration files
3. Environment-specific configurations should be handled through `.env` file

## Dependencies Analysis

### Dependencies to Remove
1. Vault-related:
   - `hvac` - Vault client
   - `flask_session` - Only needed for Vault integration

2. AWS-related:
   - `boto3` - AWS SDK
   - `botocore` - AWS SDK core

3. Optional features that can be removed if not needed:
   - `Flask-SocketIO` - If real-time features aren't used
   - `psutil` - If system monitoring isn't required
   - `oracledb`, `mysql-connector-python`, `PyMySQL` - If only using PostgreSQL

### Core Dependencies to Keep
1. Flask and WSGI:
   - `Flask`
   - `gunicorn`
   - `Werkzeug`
   - `Flask-Migrate`
   - `Flask-Caching`

2. Database (PostgreSQL focused):
   - `SQLAlchemy`
   - `Flask-SQLAlchemy`
   - `alembic`
   - `psycopg2-binary`

3. Forms and Security:
   - `Flask-WTF`
   - `Flask-Login`
   - `email-validator`
   - `WTForms-SQLAlchemy`

4. Utilities:
   - `python-dotenv`
   - `requests`
   - `python-dateutil`
   - `pytz`
   - `tzdata`

## Action Items

1. Create comprehensive database migrations that include:
   - Core table creation
   - Default data seeding
   - Role and permission setup
   - Feature-specific table creation

2. Update documentation to reflect simplified setup process

3. Archive removed scripts in case reference is needed later

4. Update README.md to document new streamlined setup process
