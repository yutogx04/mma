# Machine 1: Consul Server (Leader)

**Owner:** Your Friend  
**IP:** 10.237.235.168  
**Role:** Service Discovery Leader

---

## What This Machine Does

This machine runs the Consul server in "leader" mode. All other machines connect to it to register their services and discover each other.

---

## Install

Download Consul: https://developer.hashicorp.com/consul/downloads

Extract to `C:\consul` (Windows) or `~/consul` (Linux)

---

## No .env File Needed!

This machine doesn't run any Python/Django code.

---

## Run

### Windows
```powershell
cd C:\consul
.\consul.exe agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=10.237.235.168 -data-dir=data
```

### Linux
```bash
cd ~/consul
./consul agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -bind=10.237.235.168 -data-dir=./data
```

---

## Verify

Open browser: http://10.237.235.168:8500

You should see the Consul UI with 1 node (this machine).

---

## Troubleshooting

**Port already in use?**
- Another Consul is running. Kill it first.

**Can't access UI from other machines?**
- Check firewall allows port 8500
- Make sure `-client=0.0.0.0` is in the command
