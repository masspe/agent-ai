# Agent Builder — Backend Auto-CRUD

A powerful FastAPI backend with automatic CRUD generation for database tables.

## ✨ Features

- **Prisma-Powered Auto CRUD**: Dynamic CRUD operations for every table (single or composite primary keys) using Prisma Client Python under the hood
- **JWT Authentication**: Secure authentication with Argon2 password hashing
- **Custom User Router**: Specialized user management with password hashing (doesn't expose password_hash)
- **CORS Support**: Pre-configured for frontend integration
- **Swagger Documentation**: Interactive API documentation
- **Multi-Database Routing**: Configure multiple database URLs via environment variables and switch per request with the `X-Database` header

## 📋 Requirements

- **Python 3.12+**
- **Node.js 18+** (required by Prisma for client generation)
- **MariaDB/MySQL** database server running and accessible
- **Virtual Environment** (recommended)

## 📁 Project Structure

```
app/
├── auto_router.py          # Generic CRUD router builder backed by Prisma
├── db.py                   # Prisma client manager with multi-db support
├── dependencies.py         # get_current_user, require_admin (JWT)
├── main.py                 # FastAPI app + auto router registration
├── routers/
│   ├── auth.py            # /auth/token (login), /auth/seed_admin
│   ├── health.py          # /health/ping
│   ├── me.py              # /me (current user profile)
│   └── users.py           # User CRUD (with password hashing)
├── schema_registry.py      # Introspects table metadata via Prisma
├── security/
│   └── auth.py            # Argon2 hash/verify, create_access_token
└── utils.py               # Helpers for serialising DB rows
prisma/
└── schema.prisma          # Prisma datasource configuration
```

## 🚀 Quick Setup

### 1. Environment Setup

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
prisma generate
Copy-Item .env.example .env
```

**macOS/Linux**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
prisma generate
cp .env.example .env
```

### 2. Configuration

Edit `.env` file with your database settings:

```env
DATABASE_URL=mysql://user:pass@localhost:3306/agent_app
# Optional: JSON map of alias -> URL for multi-db routing
# DATABASES={"default":"mysql://user:pass@localhost:3306/agent_app","analytics":"mysql://user:pass@localhost:3306/analytics"}
FRONTEND_ORIGIN=http://localhost:3000
SECRET_KEY=your-long-random-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

> **Note**: If you encounter MariaDB plugin errors like `auth_gssapi_client`, switch to PyMySQL (`mysql+pymysql://...`).

### 2.1 Multi-Database Routing

When more than one URL is provided via the `DATABASES` environment variable (JSON map of `alias -> url`), Fast CRUD keeps a Prisma client open for each alias. Pick the database for a specific request by sending the `X-Database: <alias>` header. If the header is missing the default alias (from `DEFAULT_DATABASE` or the first entry) is used.

### 3. Start the Server

```bash
python -m uvicorn app.main:app --reload
# Default: http://localhost:8000
```

## 📖 API Documentation & Discovery

- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **List Routes**: http://localhost:8000/__routes (meta endpoint)
- **List Tables**: http://localhost:8000/__tables (meta endpoint)

## 🔐 Authentication

### Initial Setup

1. **Seed Admin User**:
   ```bash
   curl -X POST http://localhost:8000/auth/seed_admin
   ```
   Creates: `admin@example.com` / `admin123` (Argon2 hashed)

2. **Login**:
   ```bash
   curl -X POST http://localhost:8000/auth/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@example.com&password=admin123&grant_type=password"
   ```
   Returns: `{ "access_token": "...", "token_type": "bearer" }`

3. **Use Token**: Include in headers for protected routes:
   ```
   Authorization: Bearer <TOKEN>
   ```

## 🔄 Auto-Generated CRUD Routes

The backend automatically reflects all database tables (except excluded ones) and creates routers with:

- `GET /<table>?limit=&offset=` - List records with pagination
- `GET /<table>/{pk}` - Get single record
- `POST /<table>` - Create new record (JSON body)
- `PUT /<table>/{pk}` - Update record
- `DELETE /<table>/{pk}` - Delete record

### Composite Primary Keys

For tables with composite PKs (e.g., `listing_id` + `user_id`), the path becomes:
`/<table>/{listing_id}/{user_id}` (parameter order matches PK field order in DB)

### Examples

```bash
# List agents (authentication required)
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/agents

# Get single agent
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/agents/123

# Create agent
curl -X POST http://localhost:8000/agents \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"name":"Researcher","slug":"researcher","model":"gpt-4o","visibility":"private"}'

# Update agent
curl -X PUT http://localhost:8000/agents/123 \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"description":"New description"}'

# Delete agent
curl -X DELETE http://localhost:8000/agents/123 \
  -H "Authorization: Bearer <TOKEN>"
```

## 👥 User Management (Custom Router)

Route: `/users` (protected, admin-only by default)

Create/Update operations automatically hash passwords with Argon2 and don't expose `password_hash` in responses.

**Create User Example**:
```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" \
  -d '{"email":"new@demo.com","password":"SecretPassword!","role":"user","tenant_id":1}'
```

## 🗄️ Database Schema Management

### Adding New Tables

1. **Create Table** (via SQL or migration):
   ```sql
   CREATE TABLE report_logs (
     id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
     tenant_id BIGINT UNSIGNED NOT NULL,
     message TEXT,
     level VARCHAR(20),
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Restart Backend** (or use `--reload` for automatic restart)

3. **Verify**: Check `GET /` - the new table should appear in `auto_tables`

4. **Test New Routes**:
   - `GET /report_logs`
   - `POST /report_logs`
   - `GET /report_logs/{id}`
   - `PUT /report_logs/{id}`
   - `DELETE /report_logs/{id}`

> **Important**: Tables without primary keys won't get auto-generated routes.

### Adding Fields to Existing Tables

```sql
ALTER TABLE agents ADD COLUMN category VARCHAR(64) NULL AFTER description;
```

Restart the backend and the new field will be available in POST/PUT/GET operations.

> **Note**: Adding NOT NULL fields without defaults may cause 500/422 errors if clients don't provide the field.

## 🔒 Security & Access Control

### Table Exclusions

In `app/main.py`, tables in the `EXCLUDE` set won't get auto-routes:

```python
EXCLUDE = {"users", "alembic_version"}
```

### Admin-Only Tables

To require admin access for specific tables:

```python
deps = [Depends(get_current_user)]
if table_name in {"api_keys", "audits"}:
    deps = [Depends(require_admin)]
router = build_router_for_model(Model, table_name=table_name, pk_cols=pk_cols, dependencies=deps)
```

### Custom Routes

For tables needing custom logic, add them to `EXCLUDE` and create custom routers in `app/routers/`.

## 🌐 CORS Configuration

Configured in `main.py`:

```python
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Modify `FRONTEND_ORIGIN` or use `*` (be aware of security implications).

## 🚀 Production Deployment

1. **Use Production ASGI Server**: 
   ```bash
   gunicorn app.main:app -k uvicorn.workers.UvicornWorker
   ```

2. **Environment Variables**: Set in environment, not `.env` files

3. **Secure Secret Key**: Use long, random `SECRET_KEY`

4. **SSL/TLS**: Enable on reverse proxy (nginx, etc.)

5. **Restrict CORS**: Limit to necessary domains only

6. **Database Backups**: Regular backups and consider Alembic for migrations

## 🔧 Troubleshooting

### Common Issues

**401 Unauthorized**
- Token missing/expired → Login again with `POST /auth/token`
- Wrong header format → Use `Authorization: Bearer <TOKEN>`

**"Invalid credentials" on login**
- Using JSON instead of form-data → Use `application/x-www-form-urlencoded`
- Admin not seeded → Run `POST /auth/seed_admin`
- Wrong database → Check `DATABASE_URL`

**Authentication plugin errors (MariaDB)**
- Switch to PyMySQL: `mysql+pymysql://...` in `DATABASE_URL`

**"Unknown column" errors**
- Schema mismatch → Check column names, NOT NULL constraints, etc.

**Tables without routes**
- Missing primary key → Add PK to table
- In exclude list → Check `EXCLUDE` set in `main.py`

## 📊 Service APIs (Quick Reference)

- `GET /health/ping` → `{ "ok": true }`
- `POST /auth/seed_admin` → Create admin user
- `POST /auth/token` → Login (JWT)
- `GET /me` → Current user info
- `GET /` → List auto-mapped tables
- `GET /docs` → Swagger UI
- `GET /__routes` → List all routes (meta)
- `GET /__tables` → List database tables (meta)

## 🔮 Possible Extensions

- **Advanced Filtering**: Add `?where=...`, `?order_by=...` support to `auto_router.py`
- **Audit Logging**: Automatic logging of create/update/delete operations
- **Rate Limiting**: API rate limits and API key management
- **RBAC**: Role-based access control with granular table/operation permissions

---

For frontend integration, see `../agent_builder_frontend/README.md`.