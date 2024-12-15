#!/usr/bin/env python3
"""
Script to import plugin data and settings from a migration package.
This script will:
1. Extract migration package
2. Import plugin configurations
3. Import plugin data
4. Verify imported data
"""
import os
import sys
import json
import shutil
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

class PluginDataImporter:
    """Import plugin data from migration package."""
    
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        self.extract_dir = Path('import_temp')
        self.results = {
            'configs': [],
            'data': [],
            'static': [],
            'templates': [],
            'errors': []
        }
        
    def extract_package(self) -> bool:
        """Extract migration package."""
        try:
            # Clean up any existing temp directory
            if self.extract_dir.exists():
                shutil.rmtree(self.extract_dir)
            
            # Extract package
            with zipfile.ZipFile(self.package_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
            
            logger.info(f"Extracted package to {self.extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract package: {e}")
            return False
            
    def import_plugin_configs(self) -> bool:
        """Import plugin configurations."""
        try:
            config_file = self.extract_dir / 'configs' / 'plugin_configs.json'
            if not config_file.exists():
                raise FileNotFoundError("Plugin configurations not found in package")
            
            with open(config_file) as f:
                configs = json.load(f)
            
            for plugin_name, config in configs.items():
                try:
                    # Create plugin directory if needed
                    plugin_dir = Path('app/plugins') / plugin_name
                    plugin_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Import dependencies if any
                    if config.get('dependencies'):
                        requirements_file = plugin_dir / 'requirements.txt'
                        with open(requirements_file, 'w') as f:
                            for dep in config['dependencies']:
                                f.write(f"{dep}\n")
                    
                    self.results['configs'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to import config for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configurations: {e}")
            return False
            
    def import_plugin_data(self) -> bool:
        """Import plugin data files."""
        try:
            data_dir = self.extract_dir / 'data'
            if not data_dir.exists():
                logger.warning("No plugin data found in package")
                return True
            
            for plugin_dir in data_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                    
                try:
                    plugin_name = plugin_dir.name
                    target_dir = Path('app/plugins') / plugin_name / 'data'
                    
                    # Copy data files
                    if (plugin_dir / 'data').exists():
                        shutil.copytree(
                            plugin_dir / 'data',
                            target_dir,
                            dirs_exist_ok=True
                        )
                    
                    self.results['data'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to import data for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import plugin data: {e}")
            return False
            
    def import_static_files(self) -> bool:
        """Import plugin static files."""
        try:
            static_dir = self.extract_dir / 'static'
            if not static_dir.exists():
                logger.warning("No static files found in package")
                return True
            
            for plugin_dir in static_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                    
                try:
                    plugin_name = plugin_dir.name
                    target_dir = Path('app/plugins') / plugin_name / 'static'
                    
                    # Copy static files
                    shutil.copytree(
                        plugin_dir,
                        target_dir,
                        dirs_exist_ok=True
                    )
                    
                    self.results['static'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to import static files for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import static files: {e}")
            return False
            
    def import_templates(self) -> bool:
        """Import plugin templates."""
        try:
            templates_dir = self.extract_dir / 'templates'
            if not templates_dir.exists():
                logger.warning("No templates found in package")
                return True
            
            for plugin_dir in templates_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                    
                try:
                    plugin_name = plugin_dir.name
                    target_dir = Path('app/plugins') / plugin_name / 'templates'
                    
                    # Copy templates
                    shutil.copytree(
                        plugin_dir,
                        target_dir,
                        dirs_exist_ok=True
                    )
                    
                    self.results['templates'].append(plugin_name)
                    
                except Exception as e:
                    self.results['errors'].append(
                        f"Failed to import templates for {plugin_name}: {e}"
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import templates: {e}")
            return False
            
    def verify_import(self) -> bool:
        """Verify imported data."""
        try:
            # Load original configs
            config_file = self.extract_dir / 'configs' / 'plugin_configs.json'
            with open(config_file) as f:
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
                
                # Check static files
                if config.get('static_files'):
                    static_dir = plugin_dir / 'static'
                    for file in config['static_files']:
                        if not (static_dir / file).exists():
                            self.results['errors'].append(
                                f"Missing static file: {plugin_name}/{file}"
                            )
                
                # Check templates
                if config.get('templates'):
                    template_dir = plugin_dir / 'templates'
                    for file in config['templates']:
                        if not (template_dir / file).exists():
                            self.results['errors'].append(
                                f"Missing template: {plugin_name}/{file}"
                            )
            
            return not bool(self.results['errors'])
            
        except Exception as e:
            logger.error(f"Failed to verify import: {e}")
            return False
            
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.extract_dir.exists():
                shutil.rmtree(self.extract_dir)
        except Exception as e:
            logger.error(f"Failed to clean up: {e}")
            
    def generate_report(self) -> str:
        """Generate import report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'package': str(self.package_path),
            'results': self.results,
            'success': not bool(self.results['errors'])
        }
        
        # Save report
        os.makedirs('import_reports', exist_ok=True)
        report_path = os.path.join(
            'import_reports',
            f'import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_path
        
    def print_summary(self, report_path: str):
        """Print import summary."""
        logger.info("\nPlugin Data Import Summary:")
        logger.info("-" * 40)
        
        if self.results['configs']:
            logger.info("\nImported configurations for:")
            for plugin in self.results['configs']:
                logger.info(f"- {plugin}")
        
        if self.results['data']:
            logger.info("\nImported data for:")
            for plugin in self.results['data']:
                logger.info(f"- {plugin}")
        
        if self.results['static']:
            logger.info("\nImported static files for:")
            for plugin in self.results['static']:
                logger.info(f"- {plugin}")
        
        if self.results['templates']:
            logger.info("\nImported templates for:")
            for plugin in self.results['templates']:
                logger.info(f"- {plugin}")
        
        if self.results['errors']:
            logger.error("\nErrors encountered:")
            for error in self.results['errors']:
                logger.error(f"- {error}")
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
    def import_data(self):
        """Run complete data import process."""
        try:
            # Extract package
            if not self.extract_package():
                return False
            
            # Import everything
            self.import_plugin_configs()
            self.import_plugin_data()
            self.import_static_files()
            self.import_templates()
            
            # Verify import
            success = self.verify_import()
            
            # Generate and print report
            report_path = self.generate_report()
            self.print_summary(report_path)
            
            # Clean up
            self.cleanup()
            
            return success
            
        except Exception as e:
            logger.error(f"Data import failed: {e}")
            self.cleanup()
            return False

def main():
    """Import plugin data from migration package."""
    if len(sys.argv) != 2:
        logger.error("Usage: python import_plugin_data.py <package_path>")
        sys.exit(1)
        
    importer = PluginDataImporter(sys.argv[1])
    success = importer.import_data()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
