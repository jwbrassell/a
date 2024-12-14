storage "file" {
  path = "./vault-data"
}

listener "tcp" {
  address = "127.0.0.1:8200"
  tls_cert_file = "./instance/certs/server.crt"
  tls_key_file  = "./instance/certs/server.key"
  tls_disable_client_certs = true
}

api_addr = "https://127.0.0.1:8200"
ui = false

disable_mlock = true

# Development mode
# Warning: Do not use in production
default_lease_ttl = "168h"
max_lease_ttl = "720h"
