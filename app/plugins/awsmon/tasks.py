import boto3
import subprocess
import json
import requests
from datetime import datetime, timedelta
import time
import threading
from app.extensions import db
from app.plugins.awsmon.models import (
    EC2Instance, AWSRegion, SyntheticTest, TestResult,
    AWSCredential, ChangeLog
)
from flask import current_app
import hvac
import socket
import traceroute

class AWSMonitorTasks:
    def __init__(self, app=None):
        self.app = app
        self.stop_event = threading.Event()
        self.poll_thread = None
        self.test_thread = None
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        # Start background threads
        self.start_background_tasks()

    def start_background_tasks(self):
        """Start AWS polling and synthetic test threads"""
        if not self.poll_thread or not self.poll_thread.is_alive():
            self.poll_thread = threading.Thread(target=self.aws_poll_worker)
            self.poll_thread.daemon = True
            self.poll_thread.start()

        if not self.test_thread or not self.test_thread.is_alive():
            self.test_thread = threading.Thread(target=self.synthetic_test_worker)
            self.test_thread.daemon = True
            self.test_thread.start()

    def stop_background_tasks(self):
        """Stop background threads"""
        self.stop_event.set()
        if self.poll_thread:
            self.poll_thread.join()
        if self.test_thread:
            self.test_thread.join()

    def get_vault_client(self):
        """Get authenticated Vault client"""
        client = hvac.Client(
            url=current_app.config['VAULT_ADDR'],
            token=current_app.config['VAULT_TOKEN']
        )
        return client

    def get_aws_session(self, credential_id, region='us-east-1'):
        """Get boto3 session with credentials from Vault"""
        with self.app.app_context():
            credential = AWSCredential.query.get(credential_id)
            if not credential:
                raise ValueError(f"No credential found with ID {credential_id}")

            vault_client = self.get_vault_client()
            aws_creds = vault_client.read(credential.vault_path)
            
            if not aws_creds:
                raise ValueError(f"No credentials found at {credential.vault_path}")

            return boto3.Session(
                aws_access_key_id=aws_creds['data']['access_key'],
                aws_secret_access_key=aws_creds['data']['secret_key'],
                region_name=region
            )

    def aws_poll_worker(self):
        """Worker thread for polling AWS API"""
        while not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    self.poll_instances()
            except Exception as e:
                current_app.logger.error(f"Error in AWS polling: {str(e)}")
                current_app.logger.error(traceback.format_exc())
            
            # Wait for next poll interval
            time.sleep(60)  # Poll every minute

    def poll_instances(self):
        """Poll AWS API for instance updates"""
        for credential in AWSCredential.query.all():
            for region_code in credential.regions:
                try:
                    session = self.get_aws_session(credential.id, region_code)
                    ec2 = session.client('ec2')
                    
                    # Get region
                    region = AWSRegion.query.filter_by(code=region_code).first()
                    if not region:
                        continue

                    # Get all instances in region
                    response = ec2.describe_instances()
                    instance_map = {}
                    
                    for reservation in response['Reservations']:
                        for instance in reservation['Instances']:
                            instance_map[instance['InstanceId']] = {
                                'state': instance['State']['Name'],
                                'public_ip': instance.get('PublicIpAddress'),
                                'private_ip': instance.get('PrivateIpAddress'),
                                'type': instance['InstanceType'],
                                'launch_time': instance['LaunchTime'],
                                'tags': {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                            }
                    
                    # Update database
                    for db_instance in EC2Instance.query.filter_by(region_id=region.id):
                        if db_instance.instance_id in instance_map:
                            data = instance_map[db_instance.instance_id]
                            old_state = db_instance.state
                            db_instance.state = data['state']
                            db_instance.public_ip = data['public_ip']
                            db_instance.private_ip = data['private_ip']
                            db_instance.tags = data['tags']
                            db_instance.updated_at = datetime.utcnow()
                            
                            # Log state changes
                            if old_state != data['state']:
                                log = ChangeLog(
                                    action='update',
                                    resource_type='instance',
                                    resource_id=db_instance.instance_id,
                                    details={
                                        'old_state': old_state,
                                        'new_state': data['state']
                                    }
                                )
                                db.session.add(log)
                        else:
                            # Instance no longer exists
                            db_instance.state = 'terminated'
                            db_instance.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                
                except Exception as e:
                    current_app.logger.error(f"Error polling region {region_code}: {str(e)}")
                    current_app.logger.error(traceback.format_exc())

    def synthetic_test_worker(self):
        """Worker thread for running synthetic tests"""
        while not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    self.run_due_tests()
            except Exception as e:
                current_app.logger.error(f"Error in synthetic testing: {str(e)}")
                current_app.logger.error(traceback.format_exc())
            
            time.sleep(1)  # Check for tests every second

    def run_due_tests(self):
        """Run synthetic tests that are due"""
        now = datetime.utcnow()
        
        # Get all enabled tests
        tests = SyntheticTest.query.filter_by(enabled=True).all()
        
        for test in tests:
            # Check if test is due
            last_result = TestResult.query.filter_by(test_id=test.id)\
                .order_by(TestResult.created_at.desc())\
                .first()
            
            if last_result:
                next_run = last_result.created_at + timedelta(seconds=test.frequency)
                if next_run > now:
                    continue
            
            try:
                self.run_test(test)
            except Exception as e:
                current_app.logger.error(f"Error running test {test.id}: {str(e)}")
                current_app.logger.error(traceback.format_exc())

    def run_test(self, test):
        """Run a single synthetic test"""
        start_time = time.time()
        result = TestResult(
            test_id=test.id,
            instance_id=test.instance_id,
            status='failure'  # Default to failure
        )

        try:
            if test.test_type == 'ping':
                self.run_ping_test(test, result)
            elif test.test_type == 'traceroute':
                self.run_traceroute_test(test, result)
            elif test.test_type == 'port_check':
                self.run_port_check_test(test, result)
            elif test.test_type == 'http':
                self.run_http_test(test, result)
            
            result.response_time = (time.time() - start_time) * 1000  # Convert to ms
            
        except Exception as e:
            result.error_message = str(e)
            result.details = {'traceback': traceback.format_exc()}
        
        db.session.add(result)
        db.session.commit()

    def run_ping_test(self, test, result):
        """Run ping test"""
        try:
            # Use ping command
            output = subprocess.check_output(
                ['ping', '-c', '3', '-W', str(test.timeout), test.target],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Parse ping statistics
            stats = {}
            for line in output.split('\n'):
                if 'packets transmitted' in line:
                    parts = line.split(',')
                    stats['transmitted'] = int(parts[0].split()[0])
                    stats['received'] = int(parts[1].split()[0])
                    stats['loss'] = parts[2].split()[0]
                elif 'min/avg/max' in line:
                    times = line.split('=')[1].strip().split('/')
                    stats['min'] = float(times[0])
                    stats['avg'] = float(times[1])
                    stats['max'] = float(times[2])
            
            result.status = 'success' if stats['received'] > 0 else 'failure'
            result.details = stats
            
        except subprocess.CalledProcessError as e:
            result.status = 'failure'
            result.error_message = e.output
            result.details = {'return_code': e.returncode}

    def run_traceroute_test(self, test, result):
        """Run traceroute test"""
        try:
            # Use traceroute library
            hops = traceroute.traceroute(test.target, test.timeout)
            
            result.status = 'success'
            result.details = {
                'hops': [
                    {
                        'hop': hop.distance,
                        'ip': hop.address,
                        'name': hop.hostname,
                        'rtt': hop.rtt
                    }
                    for hop in hops
                ]
            }
            
        except Exception as e:
            result.status = 'failure'
            result.error_message = str(e)

    def run_port_check_test(self, test, result):
        """Run port check test"""
        try:
            port = test.parameters.get('port', 80)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test.timeout)
            
            # Attempt connection
            sock.connect((test.target, port))
            sock.close()
            
            result.status = 'success'
            result.details = {'port': port, 'connected': True}
            
        except socket.timeout:
            result.status = 'timeout'
            result.error_message = f"Connection to port {port} timed out"
        except Exception as e:
            result.status = 'failure'
            result.error_message = str(e)

    def run_http_test(self, test, result):
        """Run HTTP test"""
        try:
            method = test.parameters.get('method', 'GET')
            expected_status = test.parameters.get('expected_status', 200)
            
            response = requests.request(
                method,
                test.target,
                timeout=test.timeout,
                verify=False  # Skip SSL verification
            )
            
            result.status = 'success' if response.status_code == expected_status else 'failure'
            result.details = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds() * 1000,
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
            
            if result.status == 'failure':
                result.error_message = f"Expected status {expected_status}, got {response.status_code}"
            
        except requests.Timeout:
            result.status = 'timeout'
            result.error_message = "Request timed out"
        except Exception as e:
            result.status = 'failure'
            result.error_message = str(e)

# Create tasks instance
tasks = AWSMonitorTasks()
