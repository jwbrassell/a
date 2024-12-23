#!/usr/bin/env python3
from flask.cli import FlaskGroup
from app import create_app
from app.extensions import db, migrate

def create_cli_app():
    return create_app()

cli = FlaskGroup(create_app=create_cli_app)

if __name__ == "__main__":
    cli()
