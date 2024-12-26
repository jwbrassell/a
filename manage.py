#!/usr/bin/env python3
from flask.cli import FlaskGroup
from flask_migrate import Migrate
from app import create_app
from app.extensions import db
from config_migrate import MigrateConfig

app = create_app(MigrateConfig)
migrate = Migrate(app, db)

cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
