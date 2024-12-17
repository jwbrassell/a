#!/usr/bin/env python3
"""Initialize and start system monitoring."""

from app import create_app
from app.utils.system_health_monitor import system_monitor
from app.utils.alert_service import alert_service
import time
import logging
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_system():
    """Background task to monitor system health."""
    app = create_app()
    
    with app.app_context():
        while True:
            try:
                logger.info("Collecting system metrics...")
                success = system_monitor.store_metrics()
                
                if success:
                    logger.info("System metrics collected and stored successfully")
                    # Get current system status
                    status = system_monitor.get_system_status()
                    logger.info(f"System Status: {status['status']}")
                    for component, details in status['components'].items():
                        logger.info(f"{component}: {details['status']} - {details['message']}")
                else:
                    logger.error("Failed to collect system metrics")
                
                # Wait for 5 minutes before next collection
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error before retrying

def main():
    """Initialize monitoring system."""
    logger.info("Starting system monitoring...")
    
    try:
        # Start monitoring in a background thread
        monitor_thread = Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        
        logger.info("System monitoring started successfully")
        
        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring system...")
    except Exception as e:
        logger.error(f"Error starting monitoring system: {e}")
        raise

if __name__ == '__main__':
    main()
