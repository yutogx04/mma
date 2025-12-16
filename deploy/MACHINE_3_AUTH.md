# Machine 3: Auth Service

**Owner:** You  
**IP:** 10.237.235.7  
**Role:** User Authentication (Login, Register, JWT Tokens)

---

## What This Machine Does

Handles all authentication:
- User registration/login
- JWT token generation
- Token refresh

This service auto-registers 3 services in Consul:
1. users-service
2. token-service  
3. token-refresh-service

---

## Install

1. **Consul:** https://developer.hashicorp.com/consul/downloads → `C:\consul`
2. **Python 3.10+:** https://python.org
3. **Project Code:** Copy/clone mma folder → `G:\mma`
4. **Dependencies:**
   ```powershell
   cd G:\mma\mma\backend
   pip install -r requirements.txt
   ```

---

## .env File

Create/edit `G:\mma\mma\backend\.env`:

```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

# THIS machine's IP
DJANGO_HOST=10.237.235.7
DJANGO_PORT=8000

# Consul Leader (Machine 1)
CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

# RabbitMQ (Machine 4) - UPDATE WHEN YOU HAVE THE IP
RABBITMQ_HOST=10.237.235.___

SERVICE_NAME=users-service
AUTO_REGISTER_CONSUL=true
```

---

## Run (2 Terminals)

### Terminal 1 - Consul Agent

```powershell
cd C:\consul
.\consul.exe agent -bind=10.237.235.7 -retry-join=10.237.235.168 -data-dir=data
```

### Terminal 2 - Django Service

```powershell
cd G:\mma\mma\backend
python manage.py runserver 0.0.0.0:8000
```

---

## Verify

1. Consul UI: http://10.237.235.168:8500
   - Should show 3 nodes
   - Should show 3 services: users-service, token-service, token-refresh-service (all green)

2. Test locally: http://10.237.235.7:8000/health/
   - Should return health check response

---

## Troubleshooting

**Services not appearing in Consul?**
- Check `AUTO_REGISTER_CONSUL=true` (no quotes!)
- Check `DJANGO_HOST=10.237.235.7` (not 127.0.0.1)
- Check `CONSUL_HOST=10.237.235.168`

**Health check failing?**
- Make sure Django is running on 0.0.0.0:8000
