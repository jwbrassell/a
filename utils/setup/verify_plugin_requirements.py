#!/usr/bin/env python3
"""
Script to verify plugin dependencies and requirements.
This script will:
1. Check all plugin requirements
2. Verify dependency versions
3. Check for conflicts
4. Generate a requirements report
"""
import os
import sys
import json
import logging
import pkg_resources
from pathlib import Path
from typing import Dict, List, Set, Tuple
from pkg_resources import parse_requirements

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PluginRequirementsVerifier:
    """Verify plugin requirements and dependencies."""
    
    def __init__(self):
        self.plugins_dir = Path('app/plugins')
        self.results = {
            'plugins': {},
            'conflicts': [],
            'missing': [],
            'version_mismatches': []
        }
        
    def parse_requirements_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Parse requirements file into list of (package, version) tuples."""
        try:
            with open(file_path) as f:
                requirements = []
                for req in parse_requirements(f):
                    name = req.project_name
                    specs = req.specs
                    version = specs[0][1] if specs else ''
                    requirements.append((name, version))
                return requirements
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
            
    def get_installed_version(self, package: str) -> str:
        """Get installed version of a package."""
        try:
            return pkg_resources.get_distribution(package).version
        except pkg_resources.DistributionNotFound:
            return ''
            
    def check_plugin_requirements(self):
        """Check requirements for all plugins."""
        # First, get base application requirements
        base_requirements = self.parse_requirements_file(
            project_root / 'requirements.txt'
        )
        base_packages = {name: version for name, version in base_requirements}
        
        # Check each plugin
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                continue
                
            plugin_name = plugin_dir.name
            requirements_file = plugin_dir / 'requirements.txt'
            
            plugin_info = {
                'requirements': [],
                'missing': [],
                'version_mismatches': [],
                'conflicts': []
            }
            
            if requirements_file.exists():
                requirements = self.parse_requirements_file(requirements_file)
                plugin_info['requirements'] = [
                    {'package': pkg, 'version': ver}
                    for pkg, ver in requirements
                ]
                
                # Check each requirement
                for package, version in requirements:
                    installed_version = self.get_installed_version(package)
                    
                    if not installed_version:
                        plugin_info['missing'].append(package)
                        if package not in self.results['missing']:
                            self.results['missing'].append(package)
                    elif version and installed_version != version:
                        mismatch = {
                            'package': package,
                            'required': version,
                            'installed': installed_version
                        }
                        plugin_info['version_mismatches'].append(mismatch)
                        self.results['version_mismatches'].append(mismatch)
                    
                    # Check for conflicts with base requirements
                    if package in base_packages:
                        base_version = base_packages[package]
                        if version and base_version and version != base_version:
                            conflict = {
                                'package': package,
                                'plugin_version': version,
                                'base_version': base_version
                            }
                            plugin_info['conflicts'].append(conflict)
                            self.results['conflicts'].append(conflict)
            
            self.results['plugins'][plugin_name] = plugin_info
            
    def generate_report(self):
        """Generate a detailed requirements report."""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'summary': {
                'total_plugins': len(self.results['plugins']),
                'plugins_with_requirements': len([
                    p for p in self.results['plugins'].values()
                    if p['requirements']
                ]),
                'total_conflicts': len(self.results['conflicts']),
                'total_missing': len(self.results['missing']),
                'total_version_mismatches': len(self.results['version_mismatches'])
            },
            'details': self.results
        }
        
        # Save report
        os.makedirs('requirements_reports', exist_ok=True)
        report_path = os.path.join(
            'requirements_reports',
            f'requirements_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate requirements.txt with all dependencies
        all_requirements = set()
        
        # Add base requirements
        with open('requirements.txt') as f:
            all_requirements.update(f.read().splitlines())
        
        # Add plugin requirements
        for plugin_info in self.results['plugins'].values():
            for req in plugin_info['requirements']:
                package = req['package']
                version = req['version']
                if version:
                    all_requirements.add(f"{package}=={version}")
                else:
                    all_requirements.add(package)
        
        # Save complete requirements
        with open('requirements_complete.txt', 'w') as f:
            for req in sorted(all_requirements):
                f.write(f"{req}\n")
        
        return report_path
        
    def print_summary(self, report_path: str):
        """Print summary of requirements verification."""
        logger.info("\nRequirements Verification Summary:")
        logger.info("-" * 40)
        
        if self.results['conflicts']:
            logger.warning("\nConflicts found:")
            for conflict in self.results['conflicts']:
                logger.warning(
                    f"- {conflict['package']}: plugin wants {conflict['plugin_version']}, "
                    f"base requires {conflict['base_version']}"
                )
        
        if self.results['missing']:
            logger.warning("\nMissing packages:")
            for package in self.results['missing']:
                logger.warning(f"- {package}")
        
        if self.results['version_mismatches']:
            logger.warning("\nVersion mismatches:")
            for mismatch in self.results['version_mismatches']:
                logger.warning(
                    f"- {mismatch['package']}: required {mismatch['required']}, "
                    f"installed {mismatch['installed']}"
                )
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        logger.info("Complete requirements list: requirements_complete.txt")
        
    def verify_requirements(self):
        """Run complete requirements verification."""
        try:
            self.check_plugin_requirements()
            report_path = self.generate_report()
            self.print_summary(report_path)
            
            # Return success if no issues found
            return not (
                self.results['conflicts'] or
                self.results['missing'] or
                self.results['version_mismatches']
            )
            
        except Exception as e:
            logger.error(f"Requirements verification failed: {e}")
            return False

def main():
    """Verify plugin requirements."""
    verifier = PluginRequirementsVerifier()
    success = verifier.verify_requirements()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
