storage "file" {
  path = "vault-data"
}

listener "tcp" {
  address     = "127.0.0.1:8201"
  tls_disable = "true"
}

disable_mlock = true

api_addr = "http://127.0.0.1:8201"
cluster_addr = "https://127.0.0.1:8202"

ui = true

# Development mode
# DO NOT USE IN PRODUCTION
default_lease_ttl = "168h"  # 1 week
max_lease_ttl = "720h"      # 30 days
