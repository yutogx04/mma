# Consul Server (Leader) Configuration
# Run this on Machine 1 with: consul agent -config-file=consul-server.hcl

# Server mode
server = true
bootstrap_expect = 1

# Datacenter name
datacenter = "dc1"

# UI settings
ui_config {
  enabled = true
}

# Network settings - accept connections from any IP
client_addr = "0.0.0.0"

# IMPORTANT: Replace with this machine's actual IP
# Use the IP from 'ipconfig' (Windows) or 'ip addr' (Linux)
# For phone hotspot: your assigned IP like 10.237.235.X
bind_addr = "10.237.235.7"  # CHANGE THIS to your Machine 1 IP

# Data directory
data_dir = "./consul-data"

# Ports
ports {
  http = 8500
  grpc = 8502
  serf_lan = 8301
  serf_wan = 8302
  server = 8300
}

# Logging
log_level = "INFO"
