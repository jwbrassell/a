#!/bin/bash

# Exit on any error
set -e

# EC2 connection details
EC2_USER="ec2-user"
EC2_HOST="44.220.166.165"
KEY_PATH="$HOME/.ssh/mabook.pem"

# Get the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to run commands on EC2
run_remote() {
    if ! ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "$1"; then
        echo "Error: Remote command failed: $1"
        exit 1
    fi
}

# Function to copy files to EC2
copy_to_remote() {
    if ! scp -i "$KEY_PATH" -r "$1" "$EC2_USER@$EC2_HOST:$2"; then
        echo "Error: Failed to copy $1 to remote server"
        exit 1
    fi
}

# Function to check if a service or process is running
check_service() {
    local service=$1
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if [ "$service" = "vault" ]; then
            # For vault, check the process and API
            if run_remote "pgrep -f 'vault server' >/dev/null && curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null"; then
                echo "Vault is running and API is responsive"
                return 0
            fi
        else
            # For other services, use systemctl
            if run_remote "sudo systemctl is-active $service >/dev/null 2>&1"; then
                echo "Service $service is running"
                return 0
            fi
        fi
        echo "Waiting for $service to start (attempt $attempt/$max_attempts)..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "Warning: $service failed to start. Checking status..."
    if [ "$service" = "vault" ]; then
        run_remote "pgrep -f 'vault server' || echo 'No vault process found'"
        run_remote "cat ~/flask_app/vault.log"
    else
        run_remote "sudo systemctl status $service"
        run_remote "sudo journalctl -u $service --no-pager -n 50"
    fi
    return 1
}

echo "Starting infrastructure setup..."

# 1. Set up EC2 instance with required packages and services
echo "Setting up EC2 environment..."
if ! bash "$SCRIPT_DIR/ec2_setup.sh"; then
    echo "Error: EC2 setup failed"
    exit 1
fi

# 2. Create required directories
echo "Creating required directories..."
run_remote "mkdir -p ~/.vault/{data,config} && \
           mkdir -p ~/flask_app/{logs,instance}"

# 3. Copy setup scripts and configuration
echo "Copying setup files..."
copy_to_remote "$PROJECT_ROOT/setup/scripts/vault_linux.sh" "~/flask_app/setup/scripts/"
copy_to_remote "$PROJECT_ROOT/setup/scripts/app_setup.py" "~/flask_app/setup/scripts/"
copy_to_remote "$PROJECT_ROOT/flask_app.service" "~/"
run_remote "sudo mv ~/flask_app.service /etc/systemd/system/"

# 4. Set up Vault
echo "Setting up Vault..."
run_remote "cd ~/flask_app && bash setup/scripts/vault_linux.sh"

# 5. Configure and start nginx
echo "Configuring services..."
run_remote "sudo systemctl daemon-reload && \
           sudo systemctl enable nginx && \
           sudo systemctl start nginx"

# 7. Verify services are running
echo "Verifying services..."
services=("nginx" "vault")
failed_services=()

for service in "${services[@]}"; do
    if ! check_service "$service"; then
        failed_services+=("$service")
    fi
done

if [ ${#failed_services[@]} -ne 0 ]; then
    echo "Warning: The following services failed to start:"
    printf '%s\n' "${failed_services[@]}"
    echo "Please check the logs for more information:"
    echo "  sudo journalctl -u <service-name>"
fi

echo "Infrastructure setup complete!"
echo ""
echo "Next steps for application deployment:"
echo "1. Clone the repository:"
echo "   git clone [repository-url] ~/flask_app"
echo ""
echo "2. Set up Python environment:"
echo "   cd ~/flask_app"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Configure Flask app with Vault:"
echo "   python3 setup/scripts/app_setup.py"
echo ""
echo "4. Initialize database:"
echo "   flask db upgrade"
echo "   python init_database.py"
echo ""
echo "5. Start the application:"
echo "   sudo systemctl start flask_app"
echo ""
echo "To check service status:"
echo "  sudo systemctl status nginx"
echo "  sudo systemctl status vault"
echo "  sudo systemctl status flask_app"
echo ""
echo "To check logs:"
echo "  Nginx logs: sudo journalctl -u nginx"
echo "  Vault logs: sudo journalctl -u vault"
echo "  Flask app logs: sudo journalctl -u flask_app"
