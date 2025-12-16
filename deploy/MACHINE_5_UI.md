# Machine 5: UI Service (Shop)

**Owner:** TBD  
**IP:** 10.237.235.___  
**Role:** Frontend / User Interface

---

## What This Machine Does

Serves the user interface:
- Homepage (`/`)
- Admin panel (`/admin`)
- User dashboard (`/dashboard`)
- Vendor marketplace (`/vendor`)
- Static files (`/static`)

---

## Install

1. **Consul:** https://developer.hashicorp.com/consul/downloads → `C:\consul`
2. **Python 3.10+:** https://python.org
3. **Project Code:** Copy/clone mma folder
4. **Dependencies:** `pip install -r requirements.txt`

---

## .env File

Create `.env` in the backend folder:

```env
SECRET_KEY=c$2$+z)@az8*tgtu%-8_^ctn5co)!3r5=+ar2j2p(oe^hdg7h4

DEBUG=True
DB_ENGINE=sqlite

# THIS machine's IP - CHANGE THIS!
DJANGO_HOST=10.237.235.___
DJANGO_PORT=8000

# Consul Leader (Machine 1)
CONSUL_HOST=10.237.235.168
CONSUL_PORT=8500

# RabbitMQ (Machine 4) - UPDATE WHEN YOU HAVE THE IP
RABBITMQ_HOST=10.237.235.___

SERVICE_NAME=shop-service
AUTO_REGISTER_CONSUL=true
```

---

## Run (2 Terminals)

### Terminal 1 - Consul Agent
```powershell
cd C:\consul
.\consul.exe agent -bind=YOUR_IP -retry-join=10.237.235.168 -data-dir=data
```

### Terminal 2 - Shop Service
```powershell
cd path\to\mma\backend
python manage.py runserver 0.0.0.0:8000
```

---

## Verify

1. **Consul UI:** Shows shop-service (green)
2. **Local test:** http://YOUR_IP:8000 shows homepage
3. **Via Traefik:** http://MACHINE_2_IP shows homepage (routed correctly)

---

## Troubleshooting

**Service not registering?**
- Check `DJANGO_HOST` is this machine's IP
- Check `SERVICE_NAME=shop-service`
- Check `AUTO_REGISTER_CONSUL=true`

**Static files not loading?**
- This is expected when accessing via Traefik
- Works when accessing directly via machine IP
