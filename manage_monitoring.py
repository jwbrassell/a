#!/usr/bin/env python3
"""CLI tool for managing system monitoring and alerts."""

from app import create_app
from app.utils.system_health_monitor import system_monitor
from app.models.metrics import Metric, MetricAlert
from app import db
import click
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

@click.group()
def cli():
    """System monitoring management tools."""
    pass

@cli.command()
def status():
    """Show current system status."""
    with app.app_context():
        status = system_monitor.get_system_status()
        
        click.echo(f"\nSystem Status: {status['status'].upper()}")
        click.echo(f"Timestamp: {status['timestamp']}\n")
        
        for component, details in status['components'].items():
            color = {
                'healthy': 'green',
                'warning': 'yellow',
                'critical': 'red'
            }.get(details['status'], 'white')
            
            click.secho(f"{component.upper()}:", bold=True)
            click.secho(f"  Status: {details['status']}", fg=color)
            click.secho(f"  Value: {details['value']}%")
            click.secho(f"  Message: {details['message']}\n")

@cli.command()
@click.option('--hours', default=24, help='Number of hours of history to show')
def metrics(hours):
    """Show metric history."""
    with app.app_context():
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = Metric.query.filter(
            Metric.timestamp.between(start_time, end_time)
        ).order_by(Metric.timestamp.desc()).all()
        
        if not metrics:
            click.echo("No metrics found for the specified time range")
            return
        
        # Group metrics by name
        grouped_metrics = {}
        for metric in metrics:
            if metric.name not in grouped_metrics:
                grouped_metrics[metric.name] = []
            grouped_metrics[metric.name].append(metric)
        
        for name, metric_list in grouped_metrics.items():
            click.echo(f"\n{name}:")
            for metric in metric_list[:5]:  # Show last 5 readings
                click.echo(f"  {metric.timestamp}: {metric.value}")
                if metric.tags:
                    click.echo(f"  Tags: {json.dumps(metric.tags, indent=2)}")
                click.echo("")

@cli.command()
def alerts():
    """Show active alerts."""
    with app.app_context():
        alerts = MetricAlert.query.filter_by(enabled=True).all()
        
        if not alerts:
            click.echo("No active alerts configured")
            return
        
        click.echo("\nActive Alerts:")
        for alert in alerts:
            click.echo(f"\nAlert: {alert.name}")
            click.echo(f"Metric: {alert.metric_name}")
            click.echo(f"Condition: {alert.condition} {alert.threshold}")
            click.echo(f"Duration: {alert.duration} seconds")
            if alert.last_triggered:
                click.echo(f"Last Triggered: {alert.last_triggered}")
            click.echo(f"Tags: {alert.tags}")

@cli.command()
@click.argument('alert_id', type=int)
@click.option('--enable/--disable', default=True, help='Enable or disable the alert')
def toggle_alert(alert_id, enable):
    """Enable or disable an alert."""
    with app.app_context():
        alert = MetricAlert.query.get(alert_id)
        if not alert:
            click.echo(f"Alert {alert_id} not found")
            return
        
        alert.enabled = enable
        db.session.commit()
        
        status = "enabled" if enable else "disabled"
        click.echo(f"Alert '{alert.name}' has been {status}")

@cli.command()
def thresholds():
    """Show current monitoring thresholds."""
    click.echo("\nSystem Monitoring Thresholds:")
    
    for metric, levels in system_monitor.DEFAULT_THRESHOLDS.items():
        click.echo(f"\n{metric.replace('_', ' ').title()}:")
        for level, value in levels.items():
            click.echo(f"  {level}: {value}%")

if __name__ == '__main__':
    cli()
