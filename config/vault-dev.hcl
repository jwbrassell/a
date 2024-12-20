ui = true

api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"

listener "tcp" {
  address         = "127.0.0.1:8200"
  tls_disable     = "true"
}

storage "file" {
  path = "/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/vault-data"
}

# Disable mlock for development
disable_mlock = true

# Basic logging configuration
log_level = "debug"

# Development settings
default_lease_ttl = "1h"
max_lease_ttl = "24h"

# Plugin configuration
plugin_directory = "/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/vault-plugins"

# Development telemetry configuration
telemetry {
  disable_hostname = true
}
