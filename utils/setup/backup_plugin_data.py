#!/usr/bin/env python3
"""
Script to backup plugin data before making changes.
This script will:
1. Backup plugin configurations
2. Backup plugin data
3. Backup database tables
4. Create a timestamped backup archive
"""
import os
import sys
import json
import shutil
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PluginDataBackup:
    """Backup plugin data and configurations."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = Path('backups') / self.timestamp
        self.results = {
            'configs': [],
            'data': [],
            'database': [],
            'errors': []
        }
        
    def setup_backup_directory(self):
        """Create backup directory structure."""
        try:
            # Create main backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.backup_dir / 'configs').mkdir(exist_ok=True)
            (self.backup_dir / 'data').mkdir(exist_ok=True)
            (self.backup_dir / 'database').mkdir(exist_ok=True)
            
            logger.info(f"Created backup directory: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
            
    def backup_plugin_configs(self):
        """Backup plugin configurations."""
        try:
            plugins_dir = Path('app/plugins')
            configs = {}
            
            for plugin_dir in plugins_dir.iterdir():
                if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                    continue
                    
                plugin_name = plugin_dir.name
                try:
                    config = {
                        'name': plugin_name,
                        'files': [],
                        'requirements': []
                    }
                    
                    # Get all Python files
                    for file in plugin_dir.rglob('*.py'):
                        rel_path = file.relative_to(plugin_dir)
                        config['files'].append(str(rel_path))
                        
                        # Copy file to backup
                        backup_file = self.backup_dir / 'configs' / plugin_name / rel_path
                        backup_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, backup_file)
                    
                    # Get requirements if any
                    req_file = plugin_dir / 'requirements.txt'
                    if req_file.exists():
                        with open(req_file) as f:
                            config['requirements'] = [
                                line.strip() for line in f
                                if line.strip() and not line.startswith('#')
                            ]
                        
                        # Copy requirements file
                        backup_req = self.backup_dir / 'configs' / plugin_name / 'requirements.txt'
                        shutil.copy2(req_file, backup_req)
                    
                    configs[plugin_name] = config
                    self.results['configs'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to backup config for {plugin_name}: {e}"
                    )
            
            # Save configs index
            with open(self.backup_dir / 'configs' / 'index.json', 'w') as f:
                json.dump(configs, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup configurations: {e}")
            return False
            
    def backup_plugin_data(self):
        """Backup plugin data files."""
        try:
            plugins_dir = Path('app/plugins')
            
            for plugin_dir in plugins_dir.iterdir():
                if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                    continue
                    
                plugin_name = plugin_dir.name
                try:
                    # Backup data directory if exists
                    data_dir = plugin_dir / 'data'
                    if data_dir.exists():
                        backup_data = self.backup_dir / 'data' / plugin_name
                        shutil.copytree(data_dir, backup_data)
                    
                    # Backup static files
                    static_dir = plugin_dir / 'static'
                    if static_dir.exists():
                        backup_static = self.backup_dir / 'data' / plugin_name / 'static'
                        shutil.copytree(static_dir, backup_static)
                    
                    # Backup templates
                    template_dir = plugin_dir / 'templates'
                    if template_dir.exists():
                        backup_templates = self.backup_dir / 'data' / plugin_name / 'templates'
                        shutil.copytree(template_dir, backup_templates)
                    
                    self.results['data'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to backup data for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup plugin data: {e}")
            return False
            
    def backup_database(self):
        """Backup database tables."""
        try:
            db_path = Path('instance/app.db')
            if not db_path.exists():
                logger.warning("Database file not found")
                return True
            
            # Copy database file
            backup_db = self.backup_dir / 'database' / 'app.db'
            shutil.copy2(db_path, backup_db)
            
            # Export table schemas
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schemas = {}
            for (table_name,) in tables:
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                schema = cursor.fetchone()[0]
                schemas[table_name] = schema
            
            # Save schemas
            with open(self.backup_dir / 'database' / 'schemas.json', 'w') as f:
                json.dump(schemas, f, indent=2)
            
            conn.close()
            self.results['database'].append('app.db')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
            
    def create_backup_archive(self) -> str:
        """Create backup archive."""
        try:
            # Create archive name
            archive_name = f'plugin_backup_{self.timestamp}'
            
            # Create zip archive
            shutil.make_archive(
                archive_name,
                'zip',
                self.backup_dir
            )
            
            return f"{archive_name}.zip"
            
        except Exception as e:
            logger.error(f"Failed to create backup archive: {e}")
            return None
            
    def generate_report(self) -> str:
        """Generate backup report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'backup_dir': str(self.backup_dir),
            'results': self.results
        }
        
        # Save report
        report_path = self.backup_dir / 'backup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return str(report_path)
        
    def print_summary(self, report_path: str, archive_path: str = None):
        """Print backup summary."""
        logger.info("\nPlugin Data Backup Summary:")
        logger.info("-" * 40)
        
        if self.results['configs']:
            logger.info("\nBacked up configurations for:")
            for plugin in self.results['configs']:
                logger.info(f"- {plugin}")
        
        if self.results['data']:
            logger.info("\nBacked up data for:")
            for plugin in self.results['data']:
                logger.info(f"- {plugin}")
        
        if self.results['database']:
            logger.info("\nBacked up database:")
            for db in self.results['database']:
                logger.info(f"- {db}")
        
        if self.results['errors']:
            logger.error("\nErrors encountered:")
            for error in self.results['errors']:
                logger.error(f"- {error}")
        
        logger.info(f"\nBackup directory: {self.backup_dir}")
        if archive_path:
            logger.info(f"Backup archive: {archive_path}")
        logger.info(f"Backup report: {report_path}")
        
    def create_backup(self):
        """Run complete backup process."""
        try:
            # Setup backup directory
            if not self.setup_backup_directory():
                return False
            
            # Perform backups
            self.backup_plugin_configs()
            self.backup_plugin_data()
            self.backup_database()
            
            # Create archive
            archive_path = self.create_backup_archive()
            
            # Generate and print report
            report_path = self.generate_report()
            self.print_summary(report_path, archive_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

def main():
    """Create plugin data backup."""
    backup = PluginDataBackup()
    success = backup.create_backup()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
