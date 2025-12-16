# Consul Agent (Follower) Configuration  
# Run on Machines 2-5 with: consul agent -config-file=consul-agent.hcl

# Client mode (not a server)
server = false

# Datacenter name - must match server
datacenter = "dc1"

# Join the leader server
# IMPORTANT: Replace with Machine 1's actual IP
retry_join = ["10.237.235.7"]  # CHANGE to your Consul Server IP

# Network settings
client_addr = "127.0.0.1"

# IMPORTANT: Replace with THIS machine's actual IP  
# Each machine needs its own IP here
bind_addr = "10.237.235.X"  # CHANGE THIS to this machine's IP

# Data directory
data_dir = "./consul-data"

# Logging
log_level = "INFO"
