# Machine 2: Traefik (API Gateway)

**Owner:** TBD  
**IP:** 10.237.235.___  
**Role:** Reverse Proxy / Load Balancer

---

## What This Machine Does

Traefik receives all web requests and routes them to the correct service. It discovers services through Consul.

---

## Install

1. **Consul:** https://developer.hashicorp.com/consul/downloads → `C:\consul`
2. **Traefik:** https://github.com/traefik/traefik/releases → `C:\traefik`

---

## No .env File Needed!

This machine doesn't run any Python/Django code.

---

## Run (2 Terminals)

### Terminal 1 - Consul Agent

First, update YOUR_IP to this machine's actual IP:

**Windows:**
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

**Linux:**
```bash
cd ~/consul
./consul agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=./data
```

### Terminal 2 - Traefik

**Option A: Using config file (recommended)**
```powershell
cd C:\traefik
.\traefik.exe --configfile=G:\mma\mma\traefik\traefik-distributed.yml
```

**Option B: Using command-line flags**
```powershell
cd C:\traefik
.\traefik.exe --api.insecure=true --entrypoints.web.address=:80 --providers.consulCatalog.endpoint.address=10.237.235.168:8500 --providers.consulCatalog.exposedByDefault=false --providers.consulCatalog.prefix=traefik
```

**Linux:**
```bash
cd ~/traefik
./traefik --configfile=/path/to/traefik-distributed.yml
```

---

## Verify

1. Check Consul UI: http://10.237.235.168:8500 → Should show 2 nodes now
2. Check Traefik Dashboard: http://YOUR_IP:8080

---

## Troubleshooting

**Consul agent can't join?**
- Make sure Machine 1 (Consul Leader) is running first
- Check firewall allows port 8301

**Traefik shows no services?**
- Wait for other machines to start their Django services
- Check Traefik can reach Consul at 10.237.235.168:8500
