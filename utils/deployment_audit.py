#!/usr/bin/env python3
"""
Deployment audit script to verify application setup and configuration.
"""
import os
import sys
import json
import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentAuditor:
    """Audit deployment configuration and setup."""
    
    def __init__(self):
        self.results = {
            'directories': [],
            'database': [],
            'vault': [],
            'plugins': [],
            'security': [],
            'environment': []
        }
        self.all_passed = True
    
    def log_check(self, category: str, check: str, passed: bool, details: str = None):
        """Log a check result."""
        status = '✓' if passed else '✗'
        self.results[category].append({
            'check': check,
            'passed': passed,
            'details': details
        })
        if not passed:
            self.all_passed = False
        logger.info(f"{status} {check}: {details if details else ''}")

    def check_directory(self, path: str, required_mode: int = 0o755) -> bool:
        """Check if directory exists with correct permissions."""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                self.log_check('directories', f"Directory {path}", False, "Directory does not exist")
                return False
            
            mode = os.stat(path).st_mode & 0o777
            if mode != required_mode:
                self.log_check('directories', f"Directory {path} permissions", False, 
                             f"Expected {oct(required_mode)}, got {oct(mode)}")
                return False
                
            self.log_check('directories', f"Directory {path}", True)
            return True
        except Exception as e:
            self.log_check('directories', f"Directory {path}", False, str(e))
            return False

    def check_database(self) -> bool:
        """Check database setup and connectivity."""
        try:
            db_path = os.path.join('instance', 'app.db')
            if not os.path.exists(db_path):
                self.log_check('database', "Database exists", False, "Database file not found")
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['user', 'role', 'permission']
            
            for table in required_tables:
                if table not in tables:
                    self.log_check('database', f"Table {table}", False, "Table not found")
                    return False
            
            # Check admin user exists
            cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'admin'")
            admin_exists = cursor.fetchone()[0] > 0
            self.log_check('database', "Admin user exists", admin_exists)
            
            conn.close()
            return True
        except Exception as e:
            self.log_check('database', "Database check", False, str(e))
            return False

    def check_vault(self) -> bool:
        """Check Vault status and configuration."""
        try:
            # Check if Vault is running
            result = subprocess.run(['vault', 'status'], 
                                 capture_output=True, 
                                 text=True)
            vault_running = result.returncode in [0, 2]  # 0=running, 2=sealed
            self.log_check('vault', "Vault running", vault_running)
            
            # Check .env.vault exists
            env_vault_exists = os.path.exists('.env.vault')
            self.log_check('vault', ".env.vault exists", env_vault_exists)
            
            return vault_running and env_vault_exists
        except Exception as e:
            self.log_check('vault', "Vault check", False, str(e))
            return False

    def check_plugins(self) -> bool:
        """Check plugin setup and configuration."""
        try:
            plugins_dir = os.path.join('app', 'plugins')
            required_plugins = [
                'admin', 'profile', 'documents', 'projects', 'reports',
                'awsmon', 'weblinks', 'handoffs', 'oncall', 'dispatch'
            ]
            
            all_passed = True
            for plugin in required_plugins:
                plugin_dir = os.path.join(plugins_dir, plugin)
                plugin_init = os.path.join(plugin_dir, '__init__.py')
                
                if not os.path.exists(plugin_dir):
                    self.log_check('plugins', f"Plugin {plugin}", False, "Directory not found")
                    all_passed = False
                    continue
                    
                if not os.path.exists(plugin_init):
                    self.log_check('plugins', f"Plugin {plugin}", False, "__init__.py not found")
                    all_passed = False
                    continue
                    
                self.log_check('plugins', f"Plugin {plugin}", True)
            
            return all_passed
        except Exception as e:
            self.log_check('plugins', "Plugin check", False, str(e))
            return False

    def check_security(self) -> bool:
        """Check security configuration."""
        try:
            # Check sensitive file permissions
            sensitive_files = [
                ('.env', 0o600),
                ('.env.vault', 0o600),
                ('instance/app.db', 0o600)
            ]
            
            all_passed = True
            for file_path, required_mode in sensitive_files:
                if os.path.exists(file_path):
                    mode = os.stat(file_path).st_mode & 0o777
                    if mode != required_mode:
                        self.log_check('security', f"File {file_path} permissions", False,
                                     f"Expected {oct(required_mode)}, got {oct(mode)}")
                        all_passed = False
                    else:
                        self.log_check('security', f"File {file_path} permissions", True)
                else:
                    self.log_check('security', f"File {file_path}", False, "File not found")
                    all_passed = False
            
            return all_passed
        except Exception as e:
            self.log_check('security', "Security check", False, str(e))
            return False

    def check_environment(self) -> bool:
        """Check environment configuration."""
        try:
            # Check required environment files
            required_files = ['.env', '.env.vault', 'config.py']
            
            all_passed = True
            for file_path in required_files:
                if not os.path.exists(file_path):
                    self.log_check('environment', f"File {file_path}", False, "File not found")
                    all_passed = False
                else:
                    self.log_check('environment', f"File {file_path}", True)
            
            return all_passed
        except Exception as e:
            self.log_check('environment', "Environment check", False, str(e))
            return False

    def run_audit(self) -> bool:
        """Run all audit checks."""
        try:
            # Check directories
            directories = [
                'instance',
                'instance/cache',
                'logs',
                'vault-data',
                'vault-audit',
                'vault-plugins',
                'vault-backup',
                'vault-logs',
                os.path.join('app', 'static', 'uploads')
            ]
            
            for directory in directories:
                self.check_directory(directory)
            
            # Run other checks
            self.check_database()
            self.check_vault()
            self.check_plugins()
            self.check_security()
            self.check_environment()
            
            # Generate report
            report = {
                'timestamp': datetime.datetime.now().isoformat(),
                'results': self.results,
                'all_passed': self.all_passed
            }
            
            # Save report
            os.makedirs('audit_reports', exist_ok=True)
            report_path = os.path.join('audit_reports', 
                                     f'audit_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"\nAudit complete. Report saved to {report_path}")
            logger.info(f"Overall status: {'PASSED' if self.all_passed else 'FAILED'}")
            
            return self.all_passed
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return False

def main():
    """Run deployment audit."""
    auditor = DeploymentAuditor()
    success = auditor.run_audit()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
