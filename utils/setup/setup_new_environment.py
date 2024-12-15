#!/usr/bin/env python3
"""
Script to set up a new environment for the application.
This script will:
1. Run all verification tools
2. Generate a list of required actions
3. Help with initial setup
4. Provide guidance for next steps
"""
import os
import sys
import json
import logging
import subprocess
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

class EnvironmentSetup:
    """Set up new environment for application."""
    
    def __init__(self):
        self.results = {
            'verifications': {},
            'required_actions': [],
            'completed_steps': [],
            'errors': []
        }
        
    def verify_system_requirements(self) -> bool:
        """Verify system requirements."""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 8):
                self.results['required_actions'].append(
                    "Upgrade Python to version 3.8 or higher"
                )
            
            # Check for required system packages
            required_packages = ['vault', 'sqlite3']
            for package in required_packages:
                try:
                    subprocess.run(['which', package], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    self.results['required_actions'].append(
                        f"Install system package: {package}"
                    )
            
            # Check for virtual environment
            if not os.environ.get('VIRTUAL_ENV'):
                self.results['required_actions'].append(
                    "Create and activate Python virtual environment"
                )
            
            return True
        except Exception as e:
            logger.error(f"System requirements check failed: {e}")
            return False
            
    def verify_directory_structure(self) -> bool:
        """Verify directory structure."""
        try:
            required_dirs = [
                'instance',
                'instance/cache',
                'logs',
                'vault-data',
                'vault-audit',
                'vault-plugins',
                'vault-backup',
                'vault-logs',
                'app/static/uploads'
            ]
            
            for directory in required_dirs:
                if not os.path.exists(directory):
                    self.results['required_actions'].append(
                        f"Create directory: {directory}"
                    )
            
            return True
        except Exception as e:
            logger.error(f"Directory structure check failed: {e}")
            return False
            
    def verify_configuration_files(self) -> bool:
        """Verify configuration files."""
        try:
            required_files = [
                ('.env', '.env.example'),
                ('.env.vault', None),
                ('config/vault-dev.hcl', None)
            ]
            
            for file, template in required_files:
                if not os.path.exists(file):
                    if template and os.path.exists(template):
                        self.results['required_actions'].append(
                            f"Create {file} from {template}"
                        )
                    else:
                        self.results['required_actions'].append(
                            f"Create {file}"
                        )
            
            return True
        except Exception as e:
            logger.error(f"Configuration files check failed: {e}")
            return False
            
    def verify_dependencies(self) -> bool:
        """Verify Python dependencies."""
        try:
            logger.info("Running requirements verification...")
            result = subprocess.run(
                [sys.executable, 'utils/setup/verify_plugin_requirements.py'],
                capture_output=True,
                text=True
            )
            
            # Parse requirements report
            report_dir = Path('requirements_reports')
            if report_dir.exists():
                latest_report = max(report_dir.glob('*.json'), key=os.path.getctime)
                with open(latest_report) as f:
                    report = json.load(f)
                    
                if report.get('missing'):
                    for package in report['missing']:
                        self.results['required_actions'].append(
                            f"Install Python package: {package}"
                        )
                
                if report.get('conflicts'):
                    for conflict in report['conflicts']:
                        self.results['required_actions'].append(
                            f"Resolve package conflict: {conflict['package']}"
                        )
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Dependencies check failed: {e}")
            return False
            
    def verify_database(self) -> bool:
        """Verify database setup."""
        try:
            db_path = Path('instance/app.db')
            if not db_path.exists():
                self.results['required_actions'].append(
                    "Initialize database using init_db.py"
                )
            
            return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
            
    def verify_vault(self) -> bool:
        """Verify Vault setup."""
        try:
            # Check if Vault is installed
            try:
                subprocess.run(['vault', '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                self.results['required_actions'].append(
                    "Install HashiCorp Vault"
                )
                return False
            
            # Check Vault status
            try:
                subprocess.run(['vault', 'status'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                self.results['required_actions'].append(
                    "Start Vault server using setup_app.py"
                )
            
            return True
        except Exception as e:
            logger.error(f"Vault check failed: {e}")
            return False
            
    def generate_setup_script(self) -> str:
        """Generate setup script based on required actions."""
        script = "#!/bin/bash\n\n"
        script += "# Setup script generated by setup_new_environment.py\n"
        script += f"# Generated: {datetime.now().isoformat()}\n\n"
        
        # Add commands for each required action
        for action in self.results['required_actions']:
            if action.startswith("Create directory:"):
                dir_name = action.split(": ")[1]
                script += f"mkdir -p {dir_name}\n"
            elif action.startswith("Install Python package:"):
                package = action.split(": ")[1]
                script += f"pip install {package}\n"
            elif action.startswith("Create .env from"):
                script += "cp .env.example .env\n"
                script += "# TODO: Edit .env with your configuration\n"
            else:
                script += f"# TODO: {action}\n"
        
        # Add final setup steps
        script += "\n# Final setup steps\n"
        script += "python setup_app.py\n"
        script += "python init_db.py\n"
        script += "\n# Run verification\n"
        script += "python utils/setup/verify_deployment.py\n"
        
        # Save script
        script_path = 'setup_environment.sh'
        with open(script_path, 'w') as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        
        return script_path
        
    def generate_report(self) -> str:
        """Generate setup report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'success': not bool(self.results['errors'])
        }
        
        # Save report
        os.makedirs('setup_reports', exist_ok=True)
        report_path = os.path.join(
            'setup_reports',
            f'setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_path
        
    def print_summary(self, report_path: str, script_path: str):
        """Print setup summary."""
        logger.info("\nNew Environment Setup Summary:")
        logger.info("-" * 40)
        
        if self.results['required_actions']:
            logger.info("\nRequired Actions:")
            for action in self.results['required_actions']:
                logger.info(f"• {action}")
        
        if self.results['completed_steps']:
            logger.info("\nCompleted Steps:")
            for step in self.results['completed_steps']:
                logger.info(f"✓ {step}")
        
        if self.results['errors']:
            logger.error("\nErrors encountered:")
            for error in self.results['errors']:
                logger.error(f"! {error}")
        
        logger.info(f"\nSetup script generated: {script_path}")
        logger.info(f"Detailed report saved to: {report_path}")
        
        logger.info("""
Next Steps:
1. Review the setup script and make any necessary adjustments
2. Run the setup script:
   ./setup_environment.sh
3. Follow any manual steps indicated in the script
4. Run the verification script to confirm setup:
   python utils/setup/verify_deployment.py
""")
        
    def setup_environment(self):
        """Run complete environment setup process."""
        try:
            # Run all verifications
            self.verify_system_requirements()
            self.verify_directory_structure()
            self.verify_configuration_files()
            self.verify_dependencies()
            self.verify_database()
            self.verify_vault()
            
            # Generate setup script
            script_path = self.generate_setup_script()
            
            # Generate and print report
            report_path = self.generate_report()
            self.print_summary(report_path, script_path)
            
            return not bool(self.results['errors'])
            
        except Exception as e:
            logger.error(f"Environment setup failed: {e}")
            return False

def main():
    """Set up new environment."""
    setup = EnvironmentSetup()
    success = setup.setup_environment()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
