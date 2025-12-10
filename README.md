# Multi-Vendor Marketplace Application (MMA)

> **Complete Django-based E-commerce Platform with Microservices Architecture**

A comprehensive multi-vendor marketplace that allows customers to shop from multiple vendors, vendors to manage their shops and products, and admins to oversee the entire platform. Built with microservices architecture using Consul for service discovery, Traefik for routing, and RabbitMQ for async messaging.

---

## 📑 Table of Contents

- [🏗️ Architecture Overview](#-architecture-overview)
- [🎯 User Roles & Workflows](#-user-roles--workflows)
- [⚙️ Setup & Installation](#-setup--installation)
- [🚀 Running the Application](#-running-the-application)
 - [🐳 Docker Deployment](#-docker-deployment)
 - [💻 Local Development](#-local-development)
- [🧪 Testing Components](#-testing-components)
- [📡 API Documentation](#-api-documentation)
- [🔧 Configuration & Customization](#-configuration--customization)
- [🐛 Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────┐
│   Traefik   │ ← Reverse Proxy & Load Balancer
│  (Port 80)  │   Routes requests to services
└──────┬──────┘
       │
       ├──────→ Consul (Service Discovery)
       │
       └──────→ RabbitMQ (Message Broker)
                    │
          ┌─────────┴─────────┐
  payment-worker      notification-worker
          ↓                   ↓
    Process Payments    Send Notifications
```

###10 Microservices

Each Django app is registered as a separate service with dedicated routing:

| Service | Port | Routes | Purpose |
|---------|------|--------|---------|
| **users-service** | 8001 | `/api/users`, `/api/auth` | User authentication & management |
| **token-service** | 8001 | `/api/token` | JWT token generation |
| **token-refresh-service** | 8001 | `/api/token/refresh` | JWT token refresh |
| **products-service** | 8002 | `/api/products`, `/api/categories` | Product catalog |
| **orders-service** | 8003 | `/api/orders`, `/api/cart` | Shopping cart & orders |
| **payments-service** | 8004 | `/api/payments`, `/api/payment-methods` | Payment processing |
| **reviews-service** | 8005 | `/api/reviews` | Product reviews & ratings |
| **invoices-service** | 8006 | `/api/invoices` | Invoice generation |
| **notifications-service** | 8008 | `/api/notifications` | User notifications |
| **shop-service** | 8007 | `/admin`, `/dashboard`, `/static`, `/` | Admin, dashboard, static files |

### Infrastructure Components

- **Traefik** (Port 80, 443, 8080) - Reverse proxy with dynamic routing & SSL/TLS
- **Consul** (Port 8500) - Service registry & health checking
- **RabbitMQ** (Port 5672, 15672) - Message broker for async processing
- **Database** - SQLite (dev) / MySQL / PostgreSQL (configurable)

---

## 🎯 User Roles & Workflows

### 1. Customer Workflow

#### Registration & Setup
1. **Register**: Navigate to `/auth/register`
   - Provide username, email, password
   - Add payment method details (card info)
   - Role automatically set to `customer`

2. **Login**: Go to `/api/auth/login`
   - Username + password authentication
   - Redirects to customer dashboard

#### Shopping Workflow
1. **Browse Products**: `/products/` - View all available products from all vendors
2. **View Product Details**: Click on a product to see full description, price, reviews
3. **Add to Cart**: Click "Add to Cart" button
   - Creates or updates cart (Order with status='cart')
   - Can adjust quantities

4. **Review Cart**: `/api/orders/cart`
   - See all cart items
   - Update quantities or remove items
   - View total price

5. **Checkout**: Convert cart to order
   - Select payment method
   - Confirm order
   - Order status changes: `cart` → `pending`

6. **Make Payment**: `/api/payments/`
   - Select payment method
   - Process payment
   - Payment published to RabbitMQ queues:
     - `payment` queue → payment-worker processes it
     - `notifications` queue → notification-worker creates notification
   - Order status: `pending` → `paid`

7. **Track Order**: View order status on dashboard
   - `paid` → `shipped` → `delivered`

8. **Leave Review**: After delivery, rate and review products

#### Dashboard Features
- View order history
- Track current orders
- Manage payment methods
- View notifications
- See recently viewed products

---

### 2. Vendor Workflow

#### Registration & Shop Setup
1. **Register as Vendor**: `/auth/register/vendor`
   - Provide username, email, password
   - **Create shop** during registration:
     - Shop name
     - Shop description
   - Add payment method (for receiving payouts)
   - Role set to `vendor`

2. **Create Shop** (if not done during registration): `/shops/create/`
   - Only vendors without shops need this
   - Provide shop name and description

#### Product Management
1. **Create Product**: `/products/create/`
   - Fill in product form:
     - Product name
     - Description
     - Price
     - Stock quantity
     - Category
   - Product automatically linked to vendor's shop

2. **View Products**: `/products/vendor/`
   - See all products in your shop
   - Stock level indicators (low stock/out of stock warnings)
   - Order counts per product

3. **Update Product**: Click edit on any product
   - Modify name, description, price, stock
   - Only vendors can edit their own products

4. **Delete Product**: Remove products from listing
   - Confirmation required

#### Order Management
1. **View Orders**: `/vendor/orders/`
   - See orders containing your products
   - Each order creates a `VendorOrder` for your shop
   - View order status

2. **Process Orders**:
   - Mark as `processing`
   - Add tracking number
   - Mark as `shipped`
   - Mark as `delivered`

3. **Earnings Dashboard**: `/vendor/earnings/`
   - View total sales
   - See platform fees
   - Track vendor payouts
   - Payment status (`pending`, `processing`, `paid`)

#### Vendor Dashboard Features
- Total products count
- Low stock alerts (< 10 items)
- Out of stock alerts
- Recent orders from all customers
- Last 30 days sales statistics
- Revenue tracking

---

### 3. Admin Workflow

#### Access & Login
1. **Create Superuser** (first-time setup):
   ```bash
   python manage.py createsuperuser
   ```
2. **Login**: `/api/auth/login`
   - Redirects to admin dashboard

#### Platform Management
1. **Admin Dashboard**: `/admin/dashboard/`
   - Platform-wide statistics
   - Total users (customers/vendors/admins)
   - Total orders and revenue
   - Recent activity

2. **User Management**: `/admin/users/`
   - View all users
   - Change user roles
   - Activate/deactivate accounts
   - View user details and activity

3. **Product Management**: `/admin/products/`
   - View all products from all vendors
   - Can create products for any shop
   - Moderate/remove products
   - Manage categories

4. **Order Management**: `/admin/orders/`
   - View all orders platform-wide
   - Cancel orders
   - Resolve disputes
   - Track order statuses

5. **Django Admin Panel**: `/admin/`
   - Full database access
   - Model management
   - Advanced configuration

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.8+ 
- Docker & Docker Compose (for containerized deployment)
- MySQL or PostgreSQL (optional, for production)
- Git

### Step  1: Clone Repository

```bash
git clone <your-repo-url>
cd mma
```

### Step 2: Environment Configuration

1. **Copy environment template**:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Generate SECRET_KEY**:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Edit `.env` file**:
   ```env
   # REQUIRED: Paste generated secret key
   SECRET_KEY=your-generated-secret-key-here
   
   # Development mode
   DEBUG=True
   
   # Database (choose one)
   DB_ENGINE=sqlite  # Default for development
   
   # For MySQL:
   # DB_ENGINE=mysql
   # DB_NAME=mma_db
   # DB_USER=root
   # DB_PASSWORD=your_password
   # DB_HOST=localhost
   # DB_PORT=3306
   
   # For PostgreSQL:
   # DB_ENGINE=postgresql
   # DB_NAME=mma_db
   # DB_USER=postgres
   # DB_PASSWORD=your_password
   # DB_HOST=localhost
   # DB_PORT=5432
   ```

### Step 3: Database Setup

#### Option A: SQLite (Quick Start)
No additional setup needed! SQLite is ready to use.

#### Option B: MySQL
```bash
# Install MySQL (if needed)
# Windows: Download from mysql.com
# Linux: sudo apt-get install mysql-server

# Create database
mysql -u root -p
CREATE DATABASE mma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Update .env with MySQL credentials
```

#### Option C: PostgreSQL
```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
CREATE DATABASE mma_db;
\q

# Update .env with PostgreSQL credentials
```

### Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Run Migrations

```bash
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 7: Create Sample Data (Optional)

```bash
# Create user roles and permissions
python manage.py create_roles

# You can now create test users via registration
```

---

## 🚀 Running the Application

### Option  1: Docker Deployment (Recommended)

#### Start All Services

```bash
# From project root (g:/mma/mma)
docker-compose up -d
```

This starts:
- Traefik (reverse proxy)
- Consul (service registry)
- RabbitMQ (message broker)
- All 10 microservices
- 2 worker services

#### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Application** | http://localhost | Your registered user |
| **Admin** | http://localhost/admin | Superuser credentials |
| **Traefik Dashboard** | http://localhost:8080 | No auth (dev only) |
| **Consul UI** | http://localhost:8500 | No auth |
| **RabbitMQ Management** | http://localhost:15672 | guest/guest |

#### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f users-service
docker-compose logs -f payment-worker
docker-compose logs -f notification-worker
```

#### Stop Services

```bash
docker-compose down
```

---

### Option 2: Local Development (Without Docker)

For development and debugging, run services individually:

#### Step 1: Start Infrastructure

**Terminal 1 - Consul**:
```bash
# Download Consul: https://www.consul.io/downloads
consul agent -dev
# Consul UI: http://localhost:8500
```

**Terminal 2 - RabbitMQ**:
```bash
# Download RabbitMQ: https://www.rabbitmq.com/download.html
rabbitmq-server
# Management UI: http://localhost:15672 (guest/guest)
```

**Terminal 3 - Traefik** (optional, for testing routing):
```bash
cd traefik
traefik --configFile=traefik.yml
# Dashboard: http://localhost:8080
```

#### Step 2: Start Django Service

**Terminal 4 - users-service** (or any service):
```bash
cd backend

# Set environment variables (Windows PowerShell)
$env:SERVICE_NAME="users-service"
$env:DJANGO_HOST="127.0.0.1"
$env:DJANGO_PORT="8001"
$env:CONSUL_HOST="localhost"
$env:RABBITMQ_HOST="localhost"

# Run server
python manage.py runserver 8001
```

**Repeat for other services** on different ports (8002, 8003, etc.)

#### Step 3: Start Workers

**Terminal 5 - Payment Worker**:
```bash
cd backend
python manage.py start_consumer
```

**Terminal 6 - Notification Worker**:
```bash
cd backend
python manage.py start_notification_consumer
```

#### Direct Access (Without Traefik)

When running locally without Traefik, access services directly:
- http://localhost:8001/api/users
- http://localhost:8002/api/products
- http://localhost:8007/dashboard (shop-service)

---

## 🧪 Testing Components

### Test RabbitMQ Integration

1. **Access RabbitMQ Management UI**: http://localhost:15672
   - Login: `guest` / `guest`

2. **Create a Test Payment**:
   - Login as customer
   - Add products to cart
   - Complete checkout
   - Process payment

3. **Monitor Queues**:
   - Go to "Queues" tab
   - Watch `payment` and `notifications` queues
   - See messages being published and consumed
   - Check "Message rates" graph

4. **Check Worker Logs**:
   ```bash
   docker-compose logs -f payment-worker
   docker-compose logs -f notification-worker
   ```

5. **Verify Results**:
   - Order status should change to `paid`
   - Stock quantities should decrease
   - Notification should appear in user's notification list

### Test Consul Service Discovery

1. **Access Consul UI**: http://localhost:8500

2. **View Services**:
   - Click "Services" in sidebar
   - Should see all 10 services registered
   - Each with green checkmark (healthy)

3. **Check Service Details**:
   - Click on any service (e.g., "users-service")
   - View health check status
   - See service instances
   - Review Traefik tags

4. **Test Service Health**:
   ```bash
   # Check health endpoint
   curl http://localhost:8001/health/
   # Should return: {"status": "healthy"}
   ```

5. **Simulate Service Failure**:
   ```bash
   # Stop a service
   docker-compose stop products-service
   
   # Watch Consul UI - service turns red (unhealthy)
   # Traefik stops routing to it
   
   # Restart service
   docker-compose start products-service
   # Service turns green again
   ```

### Test Traefik Routing

1. **Access Traefik Dashboard**: http://localhost:8080

2. **View HTTP Routers**:
   - Click "HTTP" → "Routers"
   - See all routing rules:
     - `users-get`, `users-post`, etc.
     - `products-get`, `products-post`, etc.
   - Each shows the routing rule (Method + PathPrefix)

3. **View HTTP Services**:
   - Click "HTTP" → "Services"
   - See backend service instances
   - Check server URLs

4. **Test Routing**:
   ```bash
   # All these go through Traefik on port 80
   curl http://localhost/api/users
   curl http://localhost/api/products
   curl http://localhost/api/orders
   curl -X POST http://localhost/api/products -d "{...}"
   ```

5. **Test Method-Based Routing**:
   ```bash
   # GET request routes to products-service
   curl -X GET http://localhost/api/products
   
   # POST request routes to products-service with different router
   curl -X POST http://localhost/api/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Test"}'
   ```

### Test Database Configurations

#### Switch to MySQL:
```bash
# Update backend/.env
DB_ENGINE=mysql
DB_NAME=mma_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Run migrations
python manage.py migrate

# Test
python manage.py check
```

#### Switch to PostgreSQL:
```bash
# Update backend/.env
DB_ENGINE=postgresql
DB_NAME=mma_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Run migrations
python manage.py migrate

# Test
python manage.py check
```

---

## 📡 API Documentation

### Authentication APIs

#### Register User (Customer)
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "card_type": "credit_card",
  "card_number": "4111111111111111",
  "card_holder": "John Doe",
  "expiry_month": 12,
  "expiry_year": 2025
}
```

#### Register Vendor
```http
POST /auth/register/vendor
Content-Type: application/x-www-form-urlencoded

username=vendor1
&email=vendor@example.com
&password=secure_password
&shop_name=My Awesome Shop
&shop_description=Best products ever
&card_type=credit_card
&card_number=4111111111111111
&card_holder=Vendor Name
&expiry_month=12
&expiry_year=2025
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}
```

#### Get JWT Token
```http
POST /api/token
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /api/token/refresh
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Product APIs

#### List Products
```http
GET /api/products
```

#### Create Product (Vendor/Admin Only)
```http
POST /api/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Product Name",
  "description": "Product description",
  "price": "99.99",
  "stock_quantity": 100,
  "category_id": 1
}
```

#### Update Product
```http
PUT /api/products/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "price": "89.99",
  "stock_quantity": 95
}
```

#### Delete Product
```http
DELETE /api/products/{id}
Authorization: Bearer <token>
```

### Order APIs

#### View Cart
```http
GET /api/orders/cart
Authorization: Bearer <token>
```

#### Add to Cart
```http
POST /api/cart
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 2
}
```

#### Update Cart Item
```http
PUT /api/cart/{item_id}
Content-Type: application/json

{
  "quantity": 5
}
```

#### Remove from Cart
```http
DELETE /api/cart/{item_id}
```

#### Create Order (Checkout)
```http
POST /api/orders
Authorization: Bearer <token>
```

### Payment APIs

#### List Payment Methods
```http
GET /api/payment-methods
Authorization: Bearer <token>
```

#### Add Payment Method
```http
POST /api/payment-methods
Authorization: Bearer <token>
Content-Type: application/json

{
  "card_type": "credit_card",
  "card_number": "4111111111111111",
  "card_holder_name": "John Doe",
  "expiry_month": 12,
  "expiry_year": 2025
}
```

#### Process Payment
```http
POST /api/payments
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": 1,
  "payment_method_id": 1,
  "amount": "99.99"
}
```

---

## 🔧 Configuration & Customization

### Modify Service Registration

Services auto-register with Consul on startup. To modify registration:

**Edit**: `backend/utils/apps.py` → `UtilsConfig.ready()`

```python
if SERVICE_NAME == "your-service":
    your_tags = base_tags + [
        "traefik.http.routers.your-get.rule=Method('GET') && PathPrefix('/api/your')",
        "traefik.http.routers.your-post.rule=Method('POST') && PathPrefix('/api/your')",
        "traefik.http.services.your-service.loadbalancer.server.port=8000"
    ]
    register_django(
        service_id=f"{service_id_prefix}1",
        service_name="your-service",
        address=DJANGO_HOST,
        port=DJANGO_PORT,
        health_path="/health/",
        interval="10s",
        tags=your_tags
    )
```

### Add New Traefik Route

**Edit**: `traefik/dynamic.yml`

```yaml
http:
  routers:
    my-custom-route:
      rule: "PathPrefix(`/custom`)"
      service: "my-service"
      entryPoints:
        - web
```

### Modify RabbitMQ Queues

**Add New Queue**: `backend/payments/producer.py`

```python
def publish_to_new_queue(data):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(rabbitmq_host)
    )
    channel = connection.channel()
    channel.queue_declare(queue='my_new_queue', durable=True)
    
    message = json.dumps(data)
    channel.basic_publish(
        exchange='',
        routing_key='my_new_queue',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
```

**Add Consumer**: Create management command similar to `start_consumer.py`

### Configure HTTPS/SSL

For production with valid domain:

1. **Update** `traefik/traefik.yml`:
   ```yaml
   certificatesResolvers:
     letsencrypt:
       acme:
         email: "your-email@example.com"  # Change this
         storage: "/etc/traefik/acme.json"
         httpChallenge:
           entryPoint: web
   ```

2. **Ensure**:
   - Domain points to your server
   - Port 80 accessible for ACME challenge
   - `acme.json` has correct permissions (600)

3. **Enable HTTPS redirect** (already configured in traefik.yml)

---

## 🐛 Troubleshooting

### Service Not Appearing in Consul

**Symptoms**: Service missing from Consul UI

**Solutions**:
1. Check service logs:
   ```bash
   docker-compose logs users-service
   ```

2. Verify environment variables:
   ```bash
   docker-compose exec users-service env | grep SERVICE_NAME
   ```

3. Check `/health/` endpoint:
   ```bash
   curl http://localhost:8001/health/
   ```

4. Verify Consul is running:
   ```bash
   docker-compose ps consul
   ```

### RabbitMQ Messages Not Processing

**Symptoms**: Orders stay in "pending", payments don't complete

**Solutions**:
1. Check worker logs:
   ```bash
   docker-compose logs payment-worker
   docker-compose logs notification-worker
   ```

2. Check RabbitMQ queues at http://localhost:15672
   - Are messages accumulating?
   - Are consumers connected?

3. Restart workers:
   ```bash
   docker-compose restart payment-worker notification-worker
   ```

4. Verify RabbitMQ connection:
   ```bash
   docker-compose exec payment-worker env | grep RABBITMQ_HOST
   ```

### Traefik Not Routing Requests

**Symptoms**: 404 errors, routes not working

**Solutions**:
1. Check Traefik dashboard: http://localhost:8080
   - Are routers registered?
   - Are services listed?

2. Check service tags in Consul UI:
   - Each service should have traefik tags

3. Verify Traefik can reach Consul:
   ```bash
   docker-compose logs traefik | grep consul
   ```

4. Restart Traefik:
   ```bash
   docker-compose restart traefik
   ```

### Database Connection Errors

**Symptoms**: "No such table", connection refused

**Solutions**:

**For SQLite**:
```bash
# Run migrations
python manage.py migrate

# Check database file exists
ls backend/db.sqlite3
```

**For MySQL**:
```bash
# Test connection
mysql -h localhost -u root -p
USE mma_db;
SHOW TABLES;

# Check .env settings
cat backend/.env | grep DB_
```

**For PostgreSQL**:
```bash
# Test connection
psql -h localhost -U postgres
\c mma_db
\dt

# Check .env settings
cat backend/.env | grep DB_
```

### Permission Denied Errors

**Symptoms**: "Permission denied" when creating products, accessing pages

**Solutions**:
1. Check user role:
   - Customers cannot create products
   - Vendors need a shop to create products
   - Only admins have full access

2. Create shop (for vendors):
   ```
   Navigate to: /shops/create/
   ```

3. Verify login status:
   - Must be logged in for most operations

### Port Already in Use

**Symptoms**: "`bind: address already in use`"

**Solutions**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Change port in backend/.env
DJANGO_PORT=8009
```

### Docker Build Failures

**Symptoms**: "`ERROR [internal] load metadata`"

**Solutions**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache

# Check Dockerfile exists
ls backend/Dockerfile
```

---

## 📚 Additional Resources

### Project Structure
```
mma/
├── backend/              # Django backend
│   ├── backend/         # Main settings
│   ├── users/           # User management
│   ├── products/        # Product catalog
│   ├── orders/          # Order management
│   ├── payments/        # Payment processing
│   ├── shop/            # Vendor shops
│   ├── reviews/         # Product reviews
│   ├── invoices/        # Invoice generation
│   ├── notifications/   # Notifications
│   ├── utils/           # Consul registration, health checks
│   ├── vendor/          # Vendor-specific views
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env            # YOUR environment (not in Git)
│   └── .env.example    # Template for team
├── frontend/
│   ├── static/         # CSS, JS, images
│   └── templates/      # HTML templates
├── consul/
│   └── services/       # Service registration templates (docs)
├── traefik/
│   ├── traefik.yml     # Static config
│   ├── dynamic.yml     # Dynamic routes
│   └── acme.json       # SSL certificates
├── docker-compose.yml  # Container orchestration
├── .gitignore
├── README.md
├── SECURITY_SETUP.md   # Security guide
└── QUICK_START.md      # Quick commands
```

### Key Files

- **`backend/backend/settings.py`** - Django configuration
- **`backend/utils/apps.py`** - Service registration logic
- **`backend/config.py`** - Service ports/hosts configuration
- **`docker-compose.yml`** - Service definitions
- **`traefik/traefik.yml`** - Reverse proxy config

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | - | Django secret key (generate new) |
| `DEBUG` | No | True | Debug mode |
| `DB_ENGINE` | No | sqlite | Database: sqlite|mysql|postgresql |
| `DB_NAME` | If MySQL/PG | - | Database name |
| `DB_USER` | If MySQL/PG | - | Database user |
| `DB_PASSWORD` | If MySQL/PG | - | Database password |
| `DB_HOST` | If MySQL/PG | localhost | Database host |
| `DB_PORT` | If MySQL/PG | 3306/5432 | Database port |
| `SERVICE_NAME` | Docker only | - | Microservice identifier |
| `DJANGO_HOST` | Docker only | - | Service hostname |
| `CONSUL_HOST` | No | localhost | Consul address |
| `RABBITMQ_HOST` | No | localhost | RabbitMQ address |

---

## 🤝 Contributing & Team Collaboration

### For New Team Members

1. **Clone the repo** and follow [Setup & Installation](#-setup--installation)
2. **Create your `.env`** from `.env.example`
3. **Generate your own SECRET_KEY** (never share keys!)
4. **Choose your database** (SQLite for quick start, MySQL for production-like testing)
5. **Run migrations** and create a superuser
6. **Start coding!**

### Before Committing

1. **Never commit `.env`** files (check `.gitignore`)
2. **Test your changes** locally
3. **Update README** if adding new features
4. **Document API changes** in this README

---

## 📄 License

[Your License Here]

---

## 🙋 Need Help?

- Check [Troubleshooting](#-troubleshooting) section
- Review `SECURITY_SETUP.md` for security details
- Check `QUICK_START.md` for quick command reference
- Review service logs: `docker-compose logs -f <service-name>`

**Happy Coding! 🚀**