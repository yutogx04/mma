# Distributed Deployment Overview

> 5 machines, 5 separate guides

---

## Machine Assignments

| Machine | File | Owner | IP |
|---------|------|-------|-----|
| 1 | [MACHINE_1_CONSUL_LEADER.md](./MACHINE_1_CONSUL_LEADER.md) | Friend | 10.237.235.168 |
| 2 | [MACHINE_2_TRAEFIK.md](./MACHINE_2_TRAEFIK.md) | TBD | 10.237.235.___ |
| 3 | [MACHINE_3_AUTH.md](./MACHINE_3_AUTH.md) | You | 10.237.235.7 |
| 4 | [MACHINE_4_BUSINESS.md](./MACHINE_4_BUSINESS.md) | TBD | 10.237.235.___ |
| 5 | [MACHINE_5_UI.md](./MACHINE_5_UI.md) | TBD | 10.237.235.___ |

---

## Startup Order

**Start in this order:**

1. ⭐ Machine 1 (Consul Leader) - MUST be first!
2. Machine 2 (Traefik)
3. Machine 3 (Auth)
4. Machine 4 (Business + RabbitMQ)
5. Machine 5 (UI)

---

## Final Verification

When all machines are running:

| Check | URL |
|-------|-----|
| Consul UI | http://10.237.235.168:8500 |
| Traefik Dashboard | http://MACHINE_2_IP:8080 |
| RabbitMQ | http://MACHINE_4_IP:15672 |
| App Homepage | http://MACHINE_2_IP |

---

## Quick IP Reference

Fill in as you configure:

```
Leader (M1):    10.237.235.168
Traefik (M2):   10.237.235.___
Auth (M3):      10.237.235.7
Business (M4):  10.237.235.___
UI (M5):        10.237.235.___
```
