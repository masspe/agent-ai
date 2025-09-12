Agent Builder — Backend Auto-CRUD

Backend FastAPI con:

SQLAlchemy Automap → CRUD automatico per tutte le tabelle del DB (con PK singole o composite).

Autenticazione JWT (Argon2 per le password).

Router custom per users (hashing, non espone password_hash).

CORS verso il frontend.

Documentazione Swagger.

Funziona con MariaDB/MySQL: usa mariadb+mariadbconnector://... o mysql+pymysql://....

Requisiti

Python 3.12

MariaDB / MySQL in esecuzione e raggiungibile

(Consigliato) venv dedicato

Struttura cartelle (generata)
app/
  auto_router.py          # Builder generico di router CRUD (GET/POST/PUT/DELETE)
  db.py                   # Engine, Session, dependency get_db
  dependencies.py         # get_current_user, require_admin (JWT)
  main.py                 # FastAPI app + registrazione router auto
  models/
    base.py               # BaseApp dichiarativo (per tabella users)
    user.py               # Modello users (auth)
  routers/
    auth.py               # /auth/token (login), /auth/seed_admin
    health.py             # /health/ping
    me.py                 # /me (profilo corrente)
    users.py              # CRUD utenti (con hashing)
  security/
    auth.py               # hash/verifica Argon2, create_access_token
  utils.py                # row_to_dict (serializzazione ORM → dict)
.env.example
requirements.txt
README.md

Setup rapido
1) Creazione venv e dipendenze

Windows (PowerShell)

python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env


macOS/Linux

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

2) Configura .env

Scegli un driver e aggiorna DATABASE_URL, esempio PyMySQL:

DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/agent_app
FRONTEND_ORIGIN=http://localhost:3000
SECRET_KEY=metti_uno_stringone_lungo_e_casuale
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120


Se vedi errori di plugin MariaDB tipo auth_gssapi_client, passa a PyMySQL (mysql+pymysql://...).

3) Avvio server
python -m uvicorn app.main:app --reload
# Default: http://localhost:8000

Documentazione & scoperta API

Swagger UI: http://localhost:8000/docs

OpenAPI JSON: http://localhost:8000/openapi.json

Lista rotte (meta): aggiungi in main.py (opzionale):

from fastapi.routing import APIRoute
@app.get("/__routes", tags=["meta"])
def list_routes():
    return [{"path": r.path, "methods": sorted([m for m in r.methods if m not in {"HEAD","OPTIONS"}])}
            for r in app.routes if isinstance(r, APIRoute)]

Autenticazione

Login: POST /auth/token (form-url-encoded con username=email, password, grant_type=password)

Seed admin: POST /auth/seed_admin
Crea admin@example.com / admin123 (hash Argon2).

Esempio (curl)

curl -X POST http://localhost:8000/auth/seed_admin

curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123&grant_type=password"
# → { "access_token": "...", "token_type": "bearer" }


Usa il token su rotte protette:

Authorization: Bearer <TOKEN>

Rotte auto-generate (Auto-CRUD)

Il backend riflette tutte le tabelle presenti nel database (tranne quelle escluse) e crea per ognuna un router con:

GET /<table>?limit=&offset=

GET /<table>/{pk}

POST /<table> (body JSON con i campi della tabella)

PUT /<table>/{pk}

DELETE /<table>/{pk}

Composite PK: se la tabella ha una PK composta (es. listing_id + user_id), il path diventa:
/<table>/{listing_id}/{user_id} (ordine dei parametri = ordine dei campi PK dal DB).

Esempi
# Lista agenti (autenticazione richiesta)
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/agents

# Recupera 1 agente
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/agents/123

# Crea un agente
curl -X POST http://localhost:8000/agents \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"name":"Ricercatore","slug":"ricercatore","model":"gpt-4o","visibility":"private"}'

# Aggiorna
curl -X PUT http://localhost:8000/agents/123 \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"description":"Nuova descrizione"}'

# Elimina
curl -X DELETE http://localhost:8000/agents/123 \
  -H "Authorization: Bearer <TOKEN>"


Nota: le rotte auto non hanno (di default) filtri complessi: c’è paginazione limit/offset.
Possiamo estendere con query param where/ordinamenti se ti serve.

Tabella users (router custom)

Rotta: /users (protetta, admin-only di default).

Create/Update fa hashing Argon2 (non espone password_hash nelle risposte).

Esempio creazione:

curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" -H "Content-Type: application/json" \
  -d '{"email":"nuovo@demo.it","password":"Segretissima!","role":"user","tenant_id":1}'

Aggiungere nuove tabelle (o nuovi campi)
Nuova tabella → nuove rotte automatiche

Crea la tabella nel DB (via SQL o migrazione). Importante: definisci una PK (anche composta).
Esempio:

CREATE TABLE report_logs (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT UNSIGNED NOT NULL,
  message TEXT,
  level VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


Riavvia il backend (uvicorn --reload lo fa automaticamente al cambio file; per nuove tabelle è più sicuro un riavvio).

Chiama GET / → la tabella deve comparire in auto_tables.

Testa le nuove rotte:

GET    /report_logs
POST   /report_logs
GET    /report_logs/{id}
PUT    /report_logs/{id}
DELETE /report_logs/{id}


Se manca la PK, il router non viene creato per quella tabella.

Nuovo campo su tabella esistente

ALTER TABLE per aggiungere il campo (metti default se NOT NULL):

ALTER TABLE agents ADD COLUMN category VARCHAR(64) NULL AFTER description;


Riavvia il backend (consigliato).

Ora puoi inviare/vedere il nuovo campo in POST/PUT/GET.

Attenzione ai vincoli:

Se aggiungi un campo NOT NULL senza default, i POST potrebbero fallire con 500/422 se il client non passa quel campo.

Se aggiungi FK, assicurati che i valori esistano, altrimenti riceverai errori dal DB all’inserimento.

Sicurezza e policy per tabella

In app/main.py:

Set di tabelle escluse dall’auto-router:

EXCLUDE = {"users", "alembic_version"}


Aggiungi qui tabelle da nascondere completamente.

Per richiedere admin su alcune tabelle:

deps = [Depends(get_current_user)]
# if table_name in {"api_keys", "audits"}:
#     deps = [Depends(require_admin)]
router = build_router_for_model(Model, table_name=table_name, pk_cols=pk_cols, dependencies=deps)


Se vuoi sovrascrivere una tabella con router custom, aggiungila ad EXCLUDE e crea un file in app/routers/ con le rotte ad hoc.

CORS

Configurato in main.py:

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
  CORSMiddleware,
  allow_origins=[FRONTEND_ORIGIN],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


Modifica FRONTEND_ORIGIN (o passa * solo se consapevole dei rischi).

Produzione (note rapide)

Esegui con un ASGI server “serio” (es. uvicorn dietro nginx o gunicorn -k uvicorn.workers.UvicornWorker).

Imposta variabili .env in ambiente (no file).

Usa un segreto longo e casuale per SECRET_KEY.

Abilita SSL/TLS sul reverse proxy.

Limita CORS ai soli domini necessari.

Backup e migrazioni DB (Alembic consigliato se inizi a cambiare spesso schema lato codice).

Troubleshooting

401 Unauthorized

Token mancante/expired → rifai login POST /auth/token.

Invio errato dal frontend: ricordati Authorization: Bearer <TOKEN>.

“Invalid credentials” su /auth/token

Stai mandando JSON → deve essere x-www-form-urlencoded (username, password, grant_type=password).

Non hai seedato l’admin: fai POST /auth/seed_admin.

Stai puntando a un altro DB: controlla DATABASE_URL.

Argon2

Assicurati argon2-cffi installato (in requirements.txt).

Se avevi hash bcrypt vecchi, il login li verifica e (opzionalmente) li ri-hasha ad Argon2.

TypeError: Boolean value of this clause is not defined (SQLAlchemy)

Accade se in codice fai if not table: su un Table. Nel nostro main.py è già corretto: if table is None:.

OperationalError (2059): Authentication plugin ... (MariaDB)

Passa a mysql+pymysql://... in DATABASE_URL.

Unknown column

Lo schema DB non combacia con ciò che stai inviando/leggendo. Controlla i nomi colonna, NOT NULL senza default, ecc.

Composite PK

L’ordine dei parametri nel path è quello definito dalla PK a DB.
Esempio store_favorites(listing_id, user_id) → /store_favorites/{listing_id}/{user_id}.

Tabella senza PK

Nessuna rotta auto viene creata: aggiungi una PK (anche composta).

API di servizio (rapido promemoria)

GET /health/ping → { "ok": true }

POST /auth/seed_admin → crea admin

POST /auth/token → login (JWT)

GET /me → info utente corrente

GET / → lista tabelle auto-mappate (auto_tables)

GET /docs → Swagger UI

Estensioni possibili

Filtri & ordinamenti generici (?where=..., ?order_by=...) → da aggiungere a auto_router.py.

Audit log automatico su create/update/delete.

Rate-limit e API Keys per integrazioni esterne.

RBAC per tabella (ruoli/permessi granulari) via mappa table_name → deps.