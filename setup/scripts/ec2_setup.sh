#!/bin/bash

# EC2 connection details
EC2_USER="ec2-user"
EC2_HOST="44.220.166.165"
KEY_PATH="$HOME/.ssh/mabook.pem"

# Function to run commands on EC2
run_remote() {
    ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "$1"
}

echo "Starting EC2 environment setup..."

# Update system packages
echo "Updating system packages..."
run_remote "sudo yum update -y"

# Install required packages
echo "Installing required packages..."
run_remote "sudo yum install -y nginx python3-pip python3-devel gcc nginx openssl wget unzip curl jq"

# Setup Vault
echo "Setting up Vault..."
run_remote "
VAULT_DIR=\"\$HOME/.vault\"
VAULT_VERSION=\"1.13.3\"
VAULT_BIN=\"\$VAULT_DIR/vault\"
VAULT_CONFIG=\"\$VAULT_DIR/config.hcl\"
VAULT_DATA=\"\$VAULT_DIR/data\"
PID_FILE=\"vault.pid\"
LOG_FILE=\"vault.log\"
ENV_FILE=\".env.vault\"

# Create directories
mkdir -p \"\$VAULT_DIR\" \"\$VAULT_DATA\"

# Download and install Vault
if [ ! -f \"\$VAULT_BIN\" ]; then
    echo \"Downloading Vault...\"
    wget -O vault.zip \"https://releases.hashicorp.com/vault/\${VAULT_VERSION}/vault_\${VAULT_VERSION}_linux_amd64.zip\"
    unzip vault.zip
    mv vault \"\$VAULT_BIN\"
    rm vault.zip
    chmod +x \"\$VAULT_BIN\"
fi

# Create Vault config
cat > \"\$VAULT_CONFIG\" << 'EOFV'
storage \"file\" {
    path = \"\$VAULT_DATA\"
}

listener \"tcp\" {
    address = \"127.0.0.1:8200\"
    tls_disable = 1
}

api_addr = \"http://127.0.0.1:8200\"
ui = false
EOFV

chmod 600 \"\$VAULT_CONFIG\"

# Create systemd service for Vault
sudo tee /etc/systemd/system/vault.service << 'EOFV'
[Unit]
Description=Vault Service
After=network.target

[Service]
User=ec2-user
Group=ec2-user
ExecStart=/home/ec2-user/.vault/vault server -config=/home/ec2-user/.vault/config.hcl
ExecReload=/bin/kill -HUP \$MAINPID
Restart=on-failure
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOFV

# Start and enable Vault service
sudo systemctl daemon-reload
sudo systemctl start vault
sudo systemctl enable vault

# Wait for Vault to start
echo \"Waiting for Vault to start...\"
sleep 5

# Export Vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Initialize Vault
echo \"Initializing Vault...\"
INIT_OUTPUT=\$(\$VAULT_BIN operator init -key-shares=5 -key-threshold=3 -format=json)

# Extract root token and unseal keys
ROOT_TOKEN=\$(echo \"\$INIT_OUTPUT\" | jq -r '.root_token')
UNSEAL_KEY_1=\$(echo \"\$INIT_OUTPUT\" | jq -r '.unseal_keys_hex[0]')
UNSEAL_KEY_2=\$(echo \"\$INIT_OUTPUT\" | jq -r '.unseal_keys_hex[1]')
UNSEAL_KEY_3=\$(echo \"\$INIT_OUTPUT\" | jq -r '.unseal_keys_hex[2]')

# Save to environment file
cat > \"\$ENV_FILE\" << EOFE
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=\$ROOT_TOKEN
VAULT_UNSEAL_KEY_1=\$UNSEAL_KEY_1
VAULT_UNSEAL_KEY_2=\$UNSEAL_KEY_2
VAULT_UNSEAL_KEY_3=\$UNSEAL_KEY_3
EOFE

chmod 600 \"\$ENV_FILE\"

# Unseal Vault
echo \"Unsealing Vault...\"
\$VAULT_BIN operator unseal \$UNSEAL_KEY_1
\$VAULT_BIN operator unseal \$UNSEAL_KEY_2
\$VAULT_BIN operator unseal \$UNSEAL_KEY_3

# Echo system cards
echo \"=== VAULT SYSTEM CARDS ===\" 
echo \"Root Token: \$ROOT_TOKEN\"
echo \"Unseal Key 1: \$UNSEAL_KEY_1\"
echo \"Unseal Key 2: \$UNSEAL_KEY_2\"
echo \"Unseal Key 3: \$UNSEAL_KEY_3\"
echo \"======================\"

echo \"Vault setup complete! Credentials saved to \$ENV_FILE\"
"

# Create self-signed SSL certificate
echo "Creating self-signed SSL certificate..."
run_remote "sudo mkdir -p /etc/nginx/ssl && \
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key \
    -out /etc/nginx/ssl/nginx.crt \
    -subj '/C=US/ST=State/L=City/O=Organization/CN=localhost'"

# Configure nginx for Flask app
echo "Configuring nginx..."
cat << 'EOF' | run_remote "sudo tee /etc/nginx/conf.d/flask_app.conf"
server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    # Flask Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name localhost;
    return 301 https://\$host\$request_uri;
}
EOF

# Install Python dependencies
echo "Installing Python dependencies..."
run_remote "python3 -m pip install --user gunicorn flask"

# Create directory for the Flask app
echo "Creating application directory..."
run_remote "mkdir -p ~/flask_app"

# Create a systemd service for gunicorn
echo "Creating gunicorn systemd service..."
cat << 'EOF' | run_remote "sudo tee /etc/systemd/system/flask_app.service"
[Unit]
Description=Gunicorn instance to serve flask application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/flask_app
Environment="PATH=/home/ec2-user/.local/bin"
ExecStart=/home/ec2-user/.local/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# Start and enable services
echo "Starting services..."
run_remote "sudo systemctl start nginx && \
    sudo systemctl enable nginx && \
    sudo systemctl start flask_app && \
    sudo systemctl enable flask_app"

# Configure firewall if it's running
echo "Configuring firewall..."
run_remote "sudo yum install -y firewalld && \
    sudo systemctl start firewalld && \
    sudo systemctl enable firewalld && \
    sudo firewall-cmd --permanent --add-service=https && \
    sudo firewall-cmd --permanent --add-service=http && \
    sudo firewall-cmd --reload"

echo "Setup complete! The server is now configured with:"
echo "- Nginx with SSL (self-signed certificate)"
echo "- Gunicorn running on port 8000"
echo "- Vault running on localhost:8200"
echo "- Firewall configured for HTTP/HTTPS"
echo "- Systemd services configured and running"
echo ""
echo "Next steps:"
echo "1. Deploy your Flask application to /home/ec2-user/flask_app"
echo "2. Ensure your wsgi.py file is properly configured"
echo "3. Restart the flask_app service after deploying: sudo systemctl restart flask_app"
