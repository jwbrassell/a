import logging
from logging.config import fileConfig

from flask import current_app
from flask_migrate import Migrate
from alembic import context

# Import all models to ensure they're known to Flask-Migrate
from app.models import *
from app.blueprints.projects.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    """Get SQLAlchemy engine from current Flask app."""
    try:
        # Try to get engine from Flask-SQLAlchemy
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError, KeyError):
        # If that fails, try to get it directly from SQLAlchemy
        try:
            return current_app.extensions['sqlalchemy'].db.engine
        except (TypeError, AttributeError, KeyError):
            # If all else fails, create engine from app config
            from sqlalchemy import create_engine
            return create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])

def get_engine_url():
    """Get database URL from engine."""
    engine = get_engine()
    if engine is None:
        # Fallback to config if engine not available
        return current_app.config.get('SQLALCHEMY_DATABASE_URI')
    
    try:
        return engine.url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(engine.url).replace('%', '%%')

# add your model's MetaData object here
# for 'autogenerate' support
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions.get('migrate', None)
if target_db is None:
    from app.extensions import db
    target_db = Migrate(current_app, db)

def get_metadata():
    """Get database metadata."""
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    
    if hasattr(target_db, 'metadata'):
        return target_db.metadata
        
    # Fallback to SQLAlchemy metadata
    from app.extensions import db
    return db.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions.get('migrate', Migrate(current_app, db)).configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
