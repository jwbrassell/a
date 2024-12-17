#!/usr/bin/env python3
"""CLI utility for bulk user management operations."""

from app import create_app
from app.utils.bulk_user_operations import BulkUserOperations
import click
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

@click.group()
def cli():
    """User management CLI tools."""
    pass

@cli.command()
@click.argument('output_file', type=click.Path())
def export_users(output_file):
    """Export all users to a CSV file."""
    try:
        with app.app_context():
            csv_content = BulkUserOperations.export_users_to_csv()
            
            with open(output_file, 'w') as f:
                f.write(csv_content)
            
            logger.info(f"Successfully exported users to {output_file}")
            
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        sys.exit(1)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def import_users(input_file):
    """Import users from a CSV file."""
    try:
        with app.app_context():
            with open(input_file, 'r') as f:
                csv_content = f.read()
            
            successful, failed = BulkUserOperations.import_users_from_csv(csv_content)
            
            logger.info(f"Successfully imported {len(successful)} users")
            
            if successful:
                logger.info("\nSuccessful imports:")
                for user in successful:
                    logger.info(f"Username: {user['username']}")
                    logger.info(f"Email: {user['email']}")
                    logger.info(f"Temporary password: {user['temp_password']}")
                    logger.info("-" * 40)
            
            if failed:
                logger.error("\nFailed imports:")
                for failure in failed:
                    logger.error(f"Row: {failure['row']}")
                    logger.error(f"Error: {failure['error']}")
                    logger.error("-" * 40)
            
    except Exception as e:
        logger.error(f"Error importing users: {e}")
        sys.exit(1)

@cli.command()
def generate_template():
    """Generate a CSV template for user import."""
    try:
        template = BulkUserOperations.generate_import_template()
        print(template)
        logger.info("Copy the above template to create your import CSV file")
        
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        sys.exit(1)

@cli.command()
@click.argument('user_ids', nargs=-1, type=int)
@click.argument('role_ids', nargs=-1, type=int)
@click.option('--operation', type=click.Choice(['add', 'remove']), default='add',
              help='Operation to perform (add or remove roles)')
def batch_roles(user_ids, role_ids, operation):
    """Batch assign or remove roles for users."""
    try:
        with app.app_context():
            results = BulkUserOperations.batch_assign_roles(
                list(user_ids),
                list(role_ids),
                operation
            )
            
            logger.info(f"\nBatch role {operation} results:")
            logger.info(f"Total processed: {results['total']}")
            logger.info(f"Successful: {len(results['successful'])}")
            logger.info(f"Failed: {len(results['failed'])}")
            
            if results['successful']:
                logger.info("\nSuccessful operations:")
                for success in results['successful']:
                    logger.info(f"Username: {success['username']}")
                    logger.info(f"Email: {success['email']}")
                    logger.info(f"Current roles: {', '.join(success['roles'])}")
                    logger.info("-" * 40)
            
            if results['failed']:
                logger.error("\nFailed operations:")
                for failure in results['failed']:
                    logger.error(f"Username: {failure['username']}")
                    logger.error(f"Error: {failure['error']}")
                    logger.error("-" * 40)
            
    except Exception as e:
        logger.error(f"Error in batch role operation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
