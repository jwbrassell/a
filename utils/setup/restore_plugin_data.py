#!/usr/bin/env python3
"""
Script to restore plugin data from a backup.
This script will:
1. Extract backup archive
2. Restore plugin configurations
3. Restore plugin data
4. Restore database if needed
5. Verify restored data
"""
import os
import sys
import json
import shutil
import sqlite3
import logging
import zipfile
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

class PluginDataRestorer:
    """Restore plugin data from backup."""
    
    def __init__(self, backup_path: str):
        self.backup_path = Path(backup_path)
        self.extract_dir = Path('restore_temp')
        self.results = {
            'configs': [],
            'data': [],
            'database': [],
            'errors': []
        }
        
    def extract_backup(self) -> bool:
        """Extract backup archive."""
        try:
            # Clean up any existing temp directory
            if self.extract_dir.exists():
                shutil.rmtree(self.extract_dir)
            
            # Extract backup
            with zipfile.ZipFile(self.backup_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
            
            logger.info(f"Extracted backup to {self.extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract backup: {e}")
            return False
            
    def restore_plugin_configs(self) -> bool:
        """Restore plugin configurations."""
        try:
            config_dir = self.extract_dir / 'configs'
            if not config_dir.exists():
                raise FileNotFoundError("Configurations not found in backup")
            
            # Load config index
            with open(config_dir / 'index.json') as f:
                configs = json.load(f)
            
            for plugin_name, config in configs.items():
                try:
                    plugin_dir = Path('app/plugins') / plugin_name
                    backup_dir = config_dir / plugin_name
                    
                    # Restore Python files
                    for file_path in config['files']:
                        src = backup_dir / file_path
                        dst = plugin_dir / file_path
                        
                        if src.exists():
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dst)
                    
                    # Restore requirements
                    if config.get('requirements'):
                        req_file = backup_dir / 'requirements.txt'
                        if req_file.exists():
                            shutil.copy2(req_file, plugin_dir / 'requirements.txt')
                    
                    self.results['configs'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to restore config for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore configurations: {e}")
            return False
            
    def restore_plugin_data(self) -> bool:
        """Restore plugin data files."""
        try:
            data_dir = self.extract_dir / 'data'
            if not data_dir.exists():
                logger.warning("No data found in backup")
                return True
            
            for plugin_dir in data_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                    
                try:
                    plugin_name = plugin_dir.name
                    target_dir = Path('app/plugins') / plugin_name
                    
                    # Restore data directory
                    if (plugin_dir / 'data').exists():
                        shutil.copytree(
                            plugin_dir / 'data',
                            target_dir / 'data',
                            dirs_exist_ok=True
                        )
                    
                    # Restore static files
                    if (plugin_dir / 'static').exists():
                        shutil.copytree(
                            plugin_dir / 'static',
                            target_dir / 'static',
                            dirs_exist_ok=True
                        )
                    
                    # Restore templates
                    if (plugin_dir / 'templates').exists():
                        shutil.copytree(
                            plugin_dir / 'templates',
                            target_dir / 'templates',
                            dirs_exist_ok=True
                        )
                    
                    self.results['data'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to restore data for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore plugin data: {e}")
            return False
            
    def restore_database(self, force: bool = False) -> bool:
        """Restore database from backup."""
        try:
            db_backup = self.extract_dir / 'database' / 'app.db'
            if not db_backup.exists():
                logger.warning("No database backup found")
                return True
            
            current_db = Path('instance/app.db')
            
            # Check if current database should be overwritten
            if current_db.exists() and not force:
                logger.warning("Database exists. Use --force to overwrite")
                return True
            
            # Backup current database if it exists
            if current_db.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                shutil.copy2(
                    current_db,
                    current_db.parent / f'app.db.{timestamp}.bak'
                )
            
            # Restore database
            shutil.copy2(db_backup, current_db)
            self.results['database'].append('app.db')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
            
    def verify_restore(self) -> bool:
        """Verify restored data."""
        try:
            # Load original config index
            with open(self.extract_dir / 'configs' / 'index.json') as f:
                original_configs = json.load(f)
            
            # Verify each plugin
            for plugin_name, config in original_configs.items():
                plugin_dir = Path('app/plugins') / plugin_name
                
                # Check plugin directory exists
                if not plugin_dir.exists():
                    self.results['errors'].append(
                        f"Plugin directory not found: {plugin_name}"
                    )
                    continue
                
                # Check Python files
                for file_path in config['files']:
                    if not (plugin_dir / file_path).exists():
                        self.results['errors'].append(
                            f"Missing file: {plugin_name}/{file_path}"
                        )
                
                # Check requirements
                if config.get('requirements'):
                    if not (plugin_dir / 'requirements.txt').exists():
                        self.results['errors'].append(
                            f"Missing requirements.txt: {plugin_name}"
                        )
            
            return not bool(self.results['errors'])
            
        except Exception as e:
            logger.error(f"Failed to verify restore: {e}")
            return False
            
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.extract_dir.exists():
                shutil.rmtree(self.extract_dir)
        except Exception as e:
            logger.error(f"Failed to clean up: {e}")
            
    def generate_report(self) -> str:
        """Generate restore report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'backup_file': str(self.backup_path),
            'results': self.results,
            'success': not bool(self.results['errors'])
        }
        
        # Save report
        os.makedirs('restore_reports', exist_ok=True)
        report_path = os.path.join(
            'restore_reports',
            f'restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_path
        
    def print_summary(self, report_path: str):
        """Print restore summary."""
        logger.info("\nPlugin Data Restore Summary:")
        logger.info("-" * 40)
        
        if self.results['configs']:
            logger.info("\nRestored configurations for:")
            for plugin in self.results['configs']:
                logger.info(f"- {plugin}")
        
        if self.results['data']:
            logger.info("\nRestored data for:")
            for plugin in self.results['data']:
                logger.info(f"- {plugin}")
        
        if self.results['database']:
            logger.info("\nRestored database:")
            for db in self.results['database']:
                logger.info(f"- {db}")
        
        if self.results['errors']:
            logger.error("\nErrors encountered:")
            for error in self.results['errors']:
                logger.error(f"- {error}")
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
    def restore_data(self, force_db: bool = False):
        """Run complete restore process."""
        try:
            # Extract backup
            if not self.extract_backup():
                return False
            
            # Restore everything
            self.restore_plugin_configs()
            self.restore_plugin_data()
            self.restore_database(force_db)
            
            # Verify restore
            success = self.verify_restore()
            
            # Generate and print report
            report_path = self.generate_report()
            self.print_summary(report_path)
            
            # Clean up
            self.cleanup()
            
            return success
            
        except Exception as e:
            logger.error(f"Data restore failed: {e}")
            self.cleanup()
            return False

def main():
    """Restore plugin data from backup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore plugin data from backup")
    parser.add_argument('backup_path', help="Path to backup archive")
    parser.add_argument('--force-db', action='store_true',
                       help="Force database restore even if one exists")
    
    args = parser.parse_args()
    
    restorer = PluginDataRestorer(args.backup_path)
    success = restorer.restore_data(args.force_db)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
