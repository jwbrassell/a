#!/usr/bin/env python3
"""
Main deployment verification script.
This script will:
1. Run all verification tools
2. Aggregate results
3. Generate a comprehensive report
4. Provide recommendations
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

class DeploymentVerifier:
    """Run all deployment verification tools."""
    
    def __init__(self):
        self.results = {
            'deployment_audit': None,
            'requirements': None,
            'routes': None,
            'overall_status': 'PENDING'
        }
        
    def run_deployment_audit(self) -> bool:
        """Run deployment audit script."""
        try:
            logger.info("\nRunning deployment audit...")
            result = subprocess.run(
                [sys.executable, 'utils/deployment_audit.py'],
                capture_output=True,
                text=True
            )
            
            # Parse audit report
            report_dir = Path('audit_reports')
            if report_dir.exists():
                latest_report = max(report_dir.glob('*.json'), key=os.path.getctime)
                with open(latest_report) as f:
                    self.results['deployment_audit'] = json.load(f)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Deployment audit failed: {e}")
            return False
            
    def run_requirements_check(self) -> bool:
        """Run requirements verification."""
        try:
            logger.info("\nVerifying requirements...")
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
                    self.results['requirements'] = json.load(f)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Requirements verification failed: {e}")
            return False
            
    def run_routes_check(self) -> bool:
        """Run routes verification."""
        try:
            logger.info("\nVerifying routes...")
            result = subprocess.run(
                [sys.executable, 'utils/setup/verify_plugin_routes.py'],
                capture_output=True,
                text=True
            )
            
            # Parse routes report
            report_dir = Path('routes_reports')
            if report_dir.exists():
                latest_report = max(report_dir.glob('*.json'), key=os.path.getctime)
                with open(latest_report) as f:
                    self.results['routes'] = json.load(f)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Routes verification failed: {e}")
            return False
            
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on verification results."""
        recommendations = []
        
        # Check deployment audit results
        if self.results['deployment_audit']:
            audit = self.results['deployment_audit']
            if not audit.get('all_passed'):
                for category, issues in audit.get('results', {}).items():
                    for issue in issues:
                        if not issue.get('passed'):
                            recommendations.append(
                                f"Fix {category} issue: {issue.get('check')} - {issue.get('details')}"
                            )
        
        # Check requirements results
        if self.results['requirements']:
            reqs = self.results['requirements']
            if reqs.get('conflicts'):
                for conflict in reqs['conflicts']:
                    recommendations.append(
                        f"Resolve package conflict: {conflict['package']} - "
                        f"plugin wants {conflict['plugin_version']}, "
                        f"base requires {conflict['base_version']}"
                    )
            if reqs.get('missing'):
                for package in reqs['missing']:
                    recommendations.append(f"Install missing package: {package}")
        
        # Check routes results
        if self.results['routes']:
            routes = self.results['routes']
            if routes.get('unregistered_routes'):
                for route in routes['unregistered_routes']:
                    recommendations.append(f"Register route: {route}")
            if routes.get('permission_issues'):
                for issue in routes['permission_issues']:
                    recommendations.append(
                        f"Fix permission issue: {issue['route']} - {issue['issue']}"
                    )
        
        return recommendations
        
    def generate_report(self) -> str:
        """Generate comprehensive verification report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'recommendations': self.generate_recommendations(),
            'summary': {
                'deployment_audit': 'PASSED' if self.results['deployment_audit'] and 
                                  self.results['deployment_audit'].get('all_passed') else 'FAILED',
                'requirements': 'PASSED' if self.results['requirements'] and not (
                    self.results['requirements'].get('conflicts') or
                    self.results['requirements'].get('missing')
                ) else 'FAILED',
                'routes': 'PASSED' if self.results['routes'] and not (
                    self.results['routes'].get('unregistered_routes') or
                    self.results['routes'].get('permission_issues')
                ) else 'FAILED'
            }
        }
        
        # Set overall status
        report['overall_status'] = 'PASSED' if all(
            status == 'PASSED' for status in report['summary'].values()
        ) else 'FAILED'
        
        # Save report
        os.makedirs('verification_reports', exist_ok=True)
        report_path = os.path.join(
            'verification_reports',
            f'verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate HTML report
        html_report = f"""
        <html>
        <head>
            <title>Deployment Verification Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .recommendations {{ margin-top: 20px; }}
                .recommendation {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>Deployment Verification Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            
            <h2>Summary</h2>
            <p>Overall Status: <span class="{report['overall_status'].lower()}">{report['overall_status']}</span></p>
            <ul>
        """
        
        for check, status in report['summary'].items():
            html_report += f"""
                <li>{check}: <span class="{status.lower()}">{status}</span></li>
            """
        
        html_report += """
            </ul>
            
            <h2>Recommendations</h2>
            <div class="recommendations">
        """
        
        for rec in report['recommendations']:
            html_report += f"""
                <div class="recommendation">• {rec}</div>
            """
        
        html_report += """
            </div>
        </body>
        </html>
        """
        
        html_path = report_path.replace('.json', '.html')
        with open(html_path, 'w') as f:
            f.write(html_report)
        
        return report_path, html_path
        
    def print_summary(self, report_path: str, html_path: str):
        """Print verification summary."""
        logger.info("\nDeployment Verification Summary:")
        logger.info("-" * 40)
        
        for check, result in self.results.items():
            if check != 'overall_status':
                status = 'PASSED' if result and not any([
                    result.get('conflicts'),
                    result.get('missing'),
                    result.get('unregistered_routes'),
                    result.get('permission_issues')
                ]) else 'FAILED'
                logger.info(f"{check}: {status}")
        
        logger.info(f"\nOverall Status: {self.results['overall_status']}")
        
        if recommendations := self.generate_recommendations():
            logger.info("\nRecommendations:")
            for rec in recommendations:
                logger.info(f"• {rec}")
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        logger.info(f"HTML report saved to: {html_path}")
        
    def verify_deployment(self):
        """Run complete deployment verification."""
        try:
            # Run all verifications
            audit_passed = self.run_deployment_audit()
            reqs_passed = self.run_requirements_check()
            routes_passed = self.run_routes_check()
            
            # Set overall status
            self.results['overall_status'] = 'PASSED' if all([
                audit_passed, reqs_passed, routes_passed
            ]) else 'FAILED'
            
            # Generate and print report
            report_path, html_path = self.generate_report()
            self.print_summary(report_path, html_path)
            
            return self.results['overall_status'] == 'PASSED'
            
        except Exception as e:
            logger.error(f"Deployment verification failed: {e}")
            return False

def main():
    """Run deployment verification."""
    verifier = DeploymentVerifier()
    success = verifier.verify_deployment()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
