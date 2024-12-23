# Production Vault Configuration (Initial Non-SSL Setup)
# Modified for initial deployment without SSL certificates

storage "file" {
  path = "vault-data"
}

listener "tcp" {
  # Using same port as dev for consistency
  address     = "127.0.0.1:8200"
  tls_disable = "true"
}

# API and Cluster Addresses
api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"

# UI Configuration
ui = true

# Log Level
log_level = "INFO"

# Lease TTL Settings
max_lease_ttl = "768h"      # 32 days
default_lease_ttl = "24h"   # 1 day

# Disable mlock
disable_mlock = true

# Disable Raw Endpoints for security
raw_storage_endpoint = false

# Plugin Directory
plugin_directory = "vault-plugins"

# Audit Device Configuration
audit_device "file" {
  path = "logs/vault-audit.log"
  
  options = {
    file_path = "logs/vault-audit.log"
    log_raw = "false"
    hmac_accessor = "true"
    mode = "0600"
  }
}

# Cache Configuration
cache {
  use_auth_auth_token = "true"
}

# Rate Limiting Settings
rate_limit_stale_age = "10m"
rate_limit_exempt_paths = [
  "/v1/sys/health",
  "/v1/sys/metrics"
]

# Security Settings
disable_sealwrap = false
disable_printable_check = false

# Request Size and Duration Limits
max_request_size = 33554432     # 32MB
max_request_duration = "90s"
