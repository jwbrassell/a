ui = true

listener "tcp" {
  address         = "127.0.0.1:8201"  # Changed port to avoid conflict
  tls_disable     = 1  # Disable TLS for development
}

storage "file" {
  path = "vault-data"
}

# Disable mlock for development
disable_mlock = true

# Basic logging configuration
log_level = "info"

# Development settings
default_lease_ttl = "1h"
max_lease_ttl = "24h"

# Plugin configuration
plugin_directory = "vault-plugins"

# Development telemetry configuration
telemetry {
  disable_hostname = true
}
