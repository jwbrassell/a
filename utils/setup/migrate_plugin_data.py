#!/usr/bin/env python3
"""
Script to help migrate plugin settings and data to a new environment.
This script will:
1. Export plugin configurations
2. Export plugin data
3. Create migration instructions
"""
import os
import sys
import json
import shutil
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

class PluginMigrator:
    """Handle plugin data migration."""
    
    def __init__(self):
        self.export_dir = Path('migration_data')
        self.plugins_dir = Path('app/plugins')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def create_export_directory(self):
        """Create directory structure for exported data."""
        export_base = self.export_dir / self.timestamp
        export_base.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different types of data
        (export_base / 'configs').mkdir(exist_ok=True)
        (export_base / 'data').mkdir(exist_ok=True)
        (export_base / 'static').mkdir(exist_ok=True)
        (export_base / 'templates').mkdir(exist_ok=True)
        
        return export_base
        
    def export_plugin_configs(self, export_base: Path):
        """Export plugin configurations."""
        configs = {}
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                continue
                
            plugin_config = {
                'name': plugin_dir.name,
                'static_files': [],
                'templates': [],
                'routes': [],
                'models': [],
                'dependencies': []
            }
            
            # Check for static files
            static_dir = plugin_dir / 'static'
            if static_dir.exists():
                for file in static_dir.rglob('*'):
                    if file.is_file():
                        plugin_config['static_files'].append(
                            str(file.relative_to(static_dir))
                        )
            
            # Check for templates
            template_dir = plugin_dir / 'templates'
            if template_dir.exists():
                for file in template_dir.rglob('*'):
                    if file.is_file():
                        plugin_config['templates'].append(
                            str(file.relative_to(template_dir))
                        )
            
            # Get Python dependencies
            requirements_file = plugin_dir / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file) as f:
                    plugin_config['dependencies'] = [
                        line.strip() for line in f 
                        if line.strip() and not line.startswith('#')
                    ]
            
            configs[plugin_dir.name] = plugin_config
        
        # Save configurations
        with open(export_base / 'configs' / 'plugin_configs.json', 'w') as f:
            json.dump(configs, f, indent=2)
            
        logger.info(f"Exported configurations for {len(configs)} plugins")
        
    def export_plugin_data(self, export_base: Path):
        """Export plugin data and static files."""
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                continue
                
            plugin_name = plugin_dir.name
            plugin_export_dir = export_base / 'data' / plugin_name
            plugin_export_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy static files
            static_dir = plugin_dir / 'static'
            if static_dir.exists():
                shutil.copytree(
                    static_dir,
                    export_base / 'static' / plugin_name,
                    dirs_exist_ok=True
                )
            
            # Copy templates
            template_dir = plugin_dir / 'templates'
            if template_dir.exists():
                shutil.copytree(
                    template_dir,
                    export_base / 'templates' / plugin_name,
                    dirs_exist_ok=True
                )
            
            # Export any plugin-specific data files
            data_dir = plugin_dir / 'data'
            if data_dir.exists():
                shutil.copytree(
                    data_dir,
                    plugin_export_dir / 'data',
                    dirs_exist_ok=True
                )
        
        logger.info("Exported plugin data and static files")
        
    def create_migration_instructions(self, export_base: Path):
        """Create instructions for migrating to new environment."""
        instructions = {
            'pre_migration_steps': [
                "1. Install required system packages",
                "2. Set up Python virtual environment",
                "3. Install base application requirements",
                "4. Initialize database"
            ],
            'plugin_specific_steps': {},
            'post_migration_steps': [
                "1. Verify all plugin static files are accessible",
                "2. Check plugin routes are registered",
                "3. Validate plugin permissions",
                "4. Test plugin functionality",
                "5. Run deployment audit script"
            ]
        }
        
        # Load plugin configs
        with open(export_base / 'configs' / 'plugin_configs.json') as f:
            plugin_configs = json.load(f)
        
        # Create plugin-specific instructions
        for plugin_name, config in plugin_configs.items():
            steps = []
            
            # Add dependency installation if needed
            if config['dependencies']:
                steps.append(
                    f"Install dependencies: pip install {' '.join(config['dependencies'])}"
                )
            
            # Add static file setup if needed
            if config['static_files']:
                steps.append(
                    f"Copy static files to app/plugins/{plugin_name}/static/"
                )
            
            # Add template setup if needed
            if config['templates']:
                steps.append(
                    f"Copy templates to app/plugins/{plugin_name}/templates/"
                )
            
            instructions['plugin_specific_steps'][plugin_name] = steps
        
        # Save instructions
        with open(export_base / 'migration_instructions.json', 'w') as f:
            json.dump(instructions, f, indent=2)
            
        # Create README
        readme_content = f"""# Plugin Migration Package

Created: {datetime.now().isoformat()}

This package contains:
1. Plugin configurations (configs/)
2. Plugin data (data/)
3. Static files (static/)
4. Templates (templates/)
5. Migration instructions (migration_instructions.json)

## Migration Steps

1. Pre-migration setup:
   - Install system dependencies
   - Set up Python environment
   - Install base requirements

2. Plugin-specific setup:
   - Follow steps in migration_instructions.json
   - Install plugin dependencies
   - Copy static files and templates
   - Import plugin data

3. Post-migration verification:
   - Run deployment audit script
   - Test plugin functionality
   - Verify permissions and access

For detailed instructions, see migration_instructions.json
"""
        
        with open(export_base / 'README.md', 'w') as f:
            f.write(readme_content)
            
        logger.info("Created migration instructions and README")
        
    def create_migration_package(self):
        """Create complete migration package."""
        try:
            # Create export directory structure
            export_base = self.create_export_directory()
            
            # Export configurations and data
            self.export_plugin_configs(export_base)
            self.export_plugin_data(export_base)
            
            # Create instructions
            self.create_migration_instructions(export_base)
            
            # Create archive
            archive_name = f'plugin_migration_{self.timestamp}'
            shutil.make_archive(
                archive_name,
                'zip',
                export_base
            )
            
            logger.info(f"""
Migration package created successfully!
- Archive: {archive_name}.zip
- Contents: {export_base}

Next steps:
1. Transfer the migration package to the new environment
2. Follow the instructions in README.md
3. Run the deployment audit script to verify setup
""")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create migration package: {e}")
            return False

def main():
    """Create plugin migration package."""
    migrator = PluginMigrator()
    success = migrator.create_migration_package()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
