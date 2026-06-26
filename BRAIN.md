# Housing Data Validation System — Complete Brain Document

## What is this project?

A production-grade housing data validation system built as two microservices. Government departments upload CSV files containing housing data. The system validates every row against business rules, flags bad data with exact row numbers, saves clean data as Parquet, and tracks every job in PostgreSQL.

---

## Why each technology was chosen

| Technology | Why |
|---|---|
| Python | Best ecosystem for data processing (Pandas, Pandera) |
| FastAPI | Async, automatic docs, native dependency injection |
| PostgreSQL | ACID compliance, JSONB support, reliable |
| Pandas | Chunked CSV reading — handles millions of rows efficiently |
| Pandera | Schema-level DataFrame validation with row-level error reporting |
| Parquet | Columnar, compressed output — 5-10x smaller than CSV |
| JWT | Stateless authentication — no session storage needed |
| bcrypt | One-way password hashing — irreversible |
| httpx | Async HTTP client for microservice communication |
| Nginx | Single entry point, reverse proxy, routes traffic |
| Docker | Containerization — consistent environment everywhere |
| Jenkins | CI/CD pipeline — automated build and deploy |
| S3 | Cloud storage for CSV uploads and Parquet output |
| Monorepo | Both services in one GitHub repo — easier to manage |

---

## Project Structure

```
housing-data-validation/                ← root (monorepo)
├── auth-service/                       ← microservice 1
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     ← FastAPI entry point
│   │   ├── database.py                 ← PostgreSQL connection
│   │   ├── models.py                   ← User table
│   │   ├── schemas.py                  ← Pydantic input/output schemas
│   │   ├── auth.py                     ← JWT and bcrypt logic
│   │   └── routes.py                   ← API endpoints
│   ├── .env                            ← secrets (never commit)
│   ├── requirements.txt
│   └── venv/                           ← isolated Python environment
│
├── validation-service/                 ← microservice 2
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     ← FastAPI entry point
│   │   ├── database.py                 ← PostgreSQL connection
│   │   ├── models.py                   ← 3 tables
│   │   ├── schemas.py                  ← Pydantic schemas
│   │   ├── dependencies.py             ← JWT verification via auth-service
│   │   ├── s3.py                       ← file storage (local now, S3 later)
│   │   ├── validator.py                ← dynamic Pandera schema builder
│   │   ├── processor.py                ← chunked CSV processing
│   │   └── routes.py                   ← 4 API endpoints
│   ├── uploads/                        ← CSV uploads stored here (local)
│   │   └── output/                     ← Parquet output stored here
│   ├── .env
│   ├── requirements.txt
│   ├── test_housing.csv                ← test CSV with intentional errors
│   ├── test_upload.py                  ← end to end test script
│   └── venv/
│
├── nginx/
│   └── nginx.conf                      ← reverse proxy config
├── .gitignore
├── README.md
├── TECH_DECISIONS.md
└── BRAIN.md                            ← this file
```

---

## Architecture — The Complete Picture

```
Client (Browser / API consumer)
           ↓
    Nginx (port 80)
    ↓              ↓
/auth/*        /validate/*
    ↓              ↓
auth-service   validation-service
(port 8001)    (port 8000)
    ↓              ↓
auth_db        validation_db
(PostgreSQL)   (PostgreSQL)
                   ↓
              uploads/ folder
              (S3 in production)
```

---

## Port Map

| Service | Port | URL |
|---|---|---|
| auth-service | 8001 | http://localhost:8001 |
| validation-service | 8000 | http://localhost:8000 |
| Nginx | 80 | http://localhost |
| PostgreSQL | 5433 | localhost:5433 |

---

## Database Map

### auth_db — users table

| Column | Type | Description |
|---|---|---|
| id | Integer | Auto-increment primary key |
| email | String | Unique, indexed, required |
| hashed_password | String | bcrypt hash, never plain text |
| is_active | Boolean | Default true, soft delete |
| created_at | DateTime | Auto-set by PostgreSQL |

### validation_db — 3 tables

**validation_rules**

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| column_name | String | Which CSV column this rule applies to |
| rule_type | String | not_null, greater_than, less_than, regex, allowed_values |
| rule_value | String | The threshold or pattern to check against |
| error_message | String | What to show user when rule fails |
| is_active | Boolean | Toggle rules without deleting |
| created_at | DateTime | Auto-set |

**validation_jobs**

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| file_name | String | Original CSV filename |
| file_path | String | Where file is stored |
| status | String | pending, processing, completed, failed |
| total_rows | Integer | Total rows in CSV |
| valid_rows | Integer | Rows that passed validation |
| error_rows | Integer | Rows that failed validation |
| created_at | DateTime | When job was created |
| completed_at | DateTime | When job finished (nullable) |

**error_records**

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| job_id | Integer | Foreign key to validation_jobs |
| row_number | Integer | Exact row in CSV (for human intervention) |
| column_name | String | Which column failed |
| error_message | String | What rule failed |
| raw_value | String | The actual bad value |
| created_at | DateTime | Auto-set |

---

## API Endpoints

### auth-service (port 8001)

| Method | Endpoint | Job |
|---|---|---|
| POST | /auth/register | Create new user, hash password, save to DB |
| POST | /auth/login | Verify credentials, return JWT token |
| GET | /auth/verify | Validate JWT token, return email |
| GET | /health | Service health check |

### validation-service (port 8000)

| Method | Endpoint | Job |
|---|---|---|
| POST | /validate/upload | Upload CSV, save locally, start background processing |
| GET | /validate/status/{job_id} | Check processing status |
| GET | /validate/errors/{job_id} | Get full error report with row numbers |
| GET | /validate/rules | See all active validation rules |
| GET | /health | Service health check |

---

## Complete Request Flows

### Register Flow

```
POST /auth/register {email, password}
         ↓
Pydantic validates UserCreate schema
Bad email format? → 422 rejected
         ↓
get_db() creates database session
         ↓
Check if email already exists in PostgreSQL
Exists? → 400 "Email already registered"
         ↓
hash_password("test123") → "$2b$12$..."
         ↓
Create User object, db.add(), db.commit()
db.refresh() → gets id and created_at from PostgreSQL
         ↓
Return UserResponse (no password field)
         ↓
finally: db.close()
```

### Login Flow

```
POST /auth/login {email, password}
         ↓
Pydantic validates UserLogin schema
         ↓
get_db() creates session
         ↓
Find user by email in PostgreSQL
Not found? → 401 "Invalid email or password"
         ↓
verify_password("test123", "$2b$12$...")
No match? → 401 "Invalid email or password"
         ↓
create_access_token({sub: email, exp: now+30min})
Signs with SECRET_KEY using HS256
Returns "eyJhbGc..."
         ↓
Return {access_token, token_type: "bearer"}
         ↓
finally: db.close()
```

### CSV Upload Flow

```
POST /validate/upload
Authorization: Bearer eyJhbGc...
file: housing_data.csv
         ↓
verify_token() dependency runs first
httpx calls GET http://localhost:8001/auth/verify
with Authorization: Bearer eyJhbGc...
         ↓
auth-service checks token signature and expiry
Invalid? → 401 Unauthorized
Valid? → returns {email, valid: true}
         ↓
File type check → must be .csv
         ↓
file content read as bytes
unique filename generated with uuid4
file saved to uploads/ folder
         ↓
ValidationJob created in PostgreSQL:
  status: "pending"
  file_name: original name
  file_path: uploads/uuid_filename.csv
         ↓
background_tasks.add_task(process_csv)
         ↓
Response sent immediately:
{message, job_id, file_name, status: "pending"}
         ↓
Background processing starts:
  job.status → "processing"
  Fetch active rules from validation_rules table
  Build Pandera schema dynamically from rules
  Read CSV in chunks (5000 rows at a time)
  For each chunk:
    validate_chunk(chunk, schema)
    Collect valid rows
    Collect error records with row numbers
  Save ErrorRecords to PostgreSQL
  Save valid rows as Parquet file
  job.status → "completed"
  job.total_rows, valid_rows, error_rows → updated
```

---

## Key Concepts Explained

### JWT — How it works

```
Login → server creates token:
{
  "sub": "tanay@test.com",  ← user identity
  "exp": 1712345678         ← expiry timestamp
}
Signed with SECRET_KEY → "eyJhbGc..."

Every future request sends:
Authorization: Bearer eyJhbGc...

Server verifies:
1. Signature valid? (not tampered)
2. Not expired?
3. Extract email from payload
```

### bcrypt — Why we use it

```
Plain password: "test123"
         ↓ bcrypt with random salt
Hash: "$2b$12$xK9mN3pQr8vL2wY5zA7uBe..."

One way — can never reverse hash to password
Salt — same password gives different hash every time
Verify — bcrypt can check plain against hash without reversing
```

### Dependency Injection — How it works

```python
# FastAPI calls get_db() automatically
def register(db: Session = Depends(get_db)):
    # db is already a live session here

# FastAPI calls verify_token() automatically
async def upload_csv(email: str = Depends(verify_token)):
    # email is already verified here
```

### Chunked Processing — Why it matters

```
Without chunks:
1,000,000 rows loaded into memory → ~400MB RAM → server crashes

With chunks (5000 rows at a time):
5000 rows → validate → discard → next 5000
Memory stays ~2MB regardless of file size
```

### Dynamic Validation Rules — Why it matters

```
Without dynamic rules:
- Rules hardcoded in Python
- To change a rule → edit code → test → deploy → downtime risk

With dynamic rules:
- Rules stored in PostgreSQL
- To change a rule → UPDATE one row in database
- No code change, no deployment, instant effect
```

### Pandera — How it validates

```python
# Rules from database:
# price → greater_than → 0
# pincode → regex → ^\d{6}$

# Build schema dynamically:
schema = DataFrameSchema({
    "price": Column(checks=[Check(lambda x: float(x) > 0, element_wise=True)]),
    "pincode": Column(checks=[Check(lambda x: bool(re.match(r'^\d{6}$', x)), element_wise=True)])
})

# Validate chunk:
schema.validate(chunk, lazy=True)
# lazy=True → collect ALL errors, not just first one
# Returns failure_cases DataFrame with exact row indices
```

---

## File by File Purpose

### auth-service

**database.py**
- Reads DATABASE_URL from .env
- Creates SQLAlchemy engine (connection pool)
- SessionLocal factory for creating sessions
- get_db() generator — creates session, yields it, always closes it

**models.py**
- User class inherits from Base
- Defines users table structure
- SQLAlchemy creates table automatically on startup

**schemas.py**
- UserCreate — validates register input (email format, password required)
- UserLogin — validates login input
- Token — shape of JWT response
- TokenData — holds decoded email from JWT
- UserResponse — what we return (no password field)

**auth.py**
- hash_password() — bcrypt scrambles plain password
- verify_password() — bcrypt checks plain against hash
- create_access_token() — builds and signs JWT with SECRET_KEY
- verify_token() — decodes and validates JWT, returns TokenData

**routes.py**
- POST /register — validate → check duplicate → hash → save → return
- POST /login — validate → find user → verify password → create JWT → return
- GET /verify — extract token → decode → return email

**main.py**
- Creates FastAPI app
- Runs Base.metadata.create_all() → creates tables on startup
- Includes router with /auth prefix

### validation-service

**database.py**
- Same as auth-service but points to validation_db
- Uses Path(__file__).resolve() to find .env reliably

**models.py**
- ValidationRule — stores business rules
- ValidationJob — tracks each CSV upload job
- ErrorRecord — stores failed rows with row numbers
- ForeignKey relationship between ValidationJob and ErrorRecord

**schemas.py**
- ValidationRuleResponse — returns rule details
- ValidationJobResponse — returns job details
- ErrorRecordResponse — returns individual error
- UploadResponse — returned immediately after upload
- StatusResponse — returned when checking job status
- ErrorReportResponse — returned with full error list

**dependencies.py**
- verify_token() — async function
- Extracts Bearer token from Authorization header
- Calls auth-service /auth/verify via httpx
- Returns email if valid, raises 401 if not
- Raises 503 if auth-service is down

**s3.py**
- save_file_locally() — saves CSV bytes to uploads/ folder
- get_file_path() — returns full path for a filename
- save_parquet_locally() — converts DataFrame to Parquet, saves to uploads/output/
- (Replace with real S3 functions when AWS is set up)

**validator.py**
- build_pandera_schema() — reads rules list, builds DataFrameSchema
- Maps rule_type to Pandera Check using lambda functions
- element_wise=True — checks one cell at a time
- Wrapper functions prevent Python closure/late binding bug
- validate_chunk() — validates one chunk against schema
- lazy=True — collects all errors not just first
- Returns (valid_rows, error_records) tuple

**processor.py**
- process_csv() — the main processing function
- Updates job status throughout processing
- Fetches active rules from database
- Reads CSV in 5000-row chunks using pd.read_csv(chunksize=5000)
- dtype=str — reads all columns as strings
- fillna("") — converts NaN to empty string for not_null checks
- Calls validate_chunk() for each chunk
- Saves all errors to database in bulk
- Saves valid rows as Parquet
- Updates job with final counts and completed_at

**routes.py**
- POST /validate/upload — async, saves file, creates job, starts background task
- GET /validate/status/{job_id} — async, returns job status
- GET /validate/errors/{job_id} — async, returns error report
- GET /validate/rules — async, returns active rules

**main.py**
- Creates FastAPI app
- Imports app.models to register all 3 models with Base
- Runs create_all() to create all tables
- Includes router with /validate prefix

---

## Nginx Configuration

```
Client request → http://localhost/auth/login
         ↓
Nginx receives on port 80
         ↓
location /auth/ matches
         ↓
proxy_pass to auth-service at 172.31.160.1:8001
         ↓
auth-service responds
         ↓
Nginx forwards response to client
```

nginx.conf structure:
- events block — connection settings
- http block — contains everything HTTP related
- upstream blocks — define backend service addresses (MUST be inside http block)
- server block — defines how to handle requests
- location blocks — URL pattern matching and routing

---

## Environment Variables

### auth-service/.env
```
DATABASE_URL=postgresql://postgres:postgres123@localhost:5433/auth_db
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### validation-service/.env
```
DATABASE_URL=postgresql://postgres:postgres123@localhost:5433/validation_db
AUTH_SERVICE_URL=http://localhost:8001
UPLOAD_DIR=uploads
```

---

## Commands Reference

### Start services
```powershell
# auth-service
cd auth-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001

# validation-service
cd validation-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Nginx
docker run -d --name nginx-proxy -p 80:80 -v "${PWD}/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" nginx
```

### PostgreSQL
```powershell
psql -U postgres -h localhost -p 5433
\c auth_db        # connect to auth database
\c validation_db  # connect to validation database
\l                # list all databases
\dt               # list all tables
\q                # exit
```

### Docker
```powershell
docker ps                    # list running containers
docker logs nginx-proxy      # check nginx logs
docker stop nginx-proxy      # stop container
docker rm nginx-proxy        # remove container
docker restart nginx-proxy   # restart container
```

### Git workflow
```powershell
git add .
git commit -m "descriptive message"
git push origin main
```

---

## Validation Rules in Database

```sql
INSERT INTO validation_rules (column_name, rule_type, rule_value, error_message, is_active) VALUES
('price', 'greater_than', '0', 'Price must be greater than 0', true),
('area_sqft', 'not_null', 'true', 'Area in sqft cannot be empty', true),
('pincode', 'regex', '^\d{6}$', 'Pincode must be exactly 6 digits', true),
('bedrooms', 'greater_than', '0', 'Bedrooms must be greater than 0', true),
('status', 'allowed_values', 'active,inactive,pending', 'Status must be active, inactive or pending', true),
('city', 'not_null', 'true', 'City cannot be empty', true),
('property_id', 'not_null', 'true', 'Property ID cannot be empty', true);
```

Rule types supported:
- **not_null** — value cannot be empty or null
- **greater_than** — numeric value must be greater than rule_value
- **less_than** — numeric value must be less than rule_value
- **regex** — value must match the regex pattern
- **allowed_values** — value must be one of comma-separated list

---

## Test CSV Structure

```csv
property_id,address,city,state,pincode,area_sqft,price,bedrooms,status
```

Intentional errors in test_housing.csv:
- Row 6 — pincode: 1234 (not 6 digits)
- Row 7 — area_sqft: empty (null violation)
- Row 8 — price: -500000 (not greater than 0)
- Row 9 — status: deleted (not in allowed values)
- Row 10 — bedrooms: empty (null violation)

Expected result: 5 valid rows, 5 error rows

---

## What is Remaining

| Feature | Status |
|---|---|
| auth-service | ✅ Complete |
| validation-service | ✅ Complete |
| Dynamic Pandera validation | ✅ Complete |
| Chunked CSV processing | ✅ Complete |
| Error reporting with row numbers | ✅ Complete |
| Parquet output | ✅ Complete |
| Nginx reverse proxy | 🔄 In progress (502 fix pending) |
| Docker containerization | ⏳ Pending |
| Jenkins CI/CD | ⏳ Pending |
| AWS S3 integration | ⏳ Pending (needs AWS account) |
| Generate fake housing dataset | ⏳ Pending |
| README with architecture diagram | ⏳ Pending |

---

## Known Issues and Fixes Applied

| Issue | Root Cause | Fix Applied |
|---|---|---|
| bcrypt error on register | passlib version conflict | pip install bcrypt==4.0.1 passlib==1.7.4 |
| DATABASE_URL is None | .env not found by uvicorn | Path(__file__).resolve().parent.parent / ".env" |
| Pandera Check.notna() not found | Pandera 0.31 changed API | Use lambda functions with element_wise=True |
| not_null not catching empty cells | NaN not matching string checks | chunk.fillna("") in processor.py |
| StatusResponse job_id missing | Schema used job_id but model has id | Changed schema to use id field |
| Nginx 502 bad gateway | upstream blocks outside http block | Moved upstream blocks inside http block |
| Nginx still using old IP | nginx.conf not reloaded properly | docker stop → docker rm → docker run fresh |

---

## Interview Questions and Answers

**"Walk me through your project architecture"**
> "It's a monorepo with two FastAPI microservices. auth-service handles JWT-based authentication — register, login, and token verification. validation-service handles CSV processing — it accepts file uploads, validates data against dynamic business rules stored in PostgreSQL using Pandera, processes files in chunks of 5000 rows to handle millions of rows efficiently, saves valid rows as Parquet to S3, and reports exact row numbers for failed records. Nginx sits in front as a reverse proxy routing /auth/* to auth-service and /validate/* to validation-service."

**"How do your microservices communicate?"**
> "validation-service calls auth-service over HTTP using httpx — an async HTTP client. For every protected request, validation-service forwards the Bearer token to auth-service's /auth/verify endpoint. Auth-service decodes the JWT, checks signature and expiry, and returns the user's email if valid. This is implemented as a FastAPI dependency using Depends() so token verification happens automatically before any route logic runs."

**"How did you implement dynamic validation rules?"**
> "Rules are stored in a PostgreSQL table with columns for column_name, rule_type, rule_value and error_message. At processing time we fetch all active rules and build a Pandera DataFrameSchema dynamically. Each rule_type maps to a lambda function — not_null checks for empty strings, greater_than converts to float and compares, regex uses re.match(), allowed_values checks membership in a list. Rules can be changed in the database without any code deployment."

**"How did you handle large CSV files?"**
> "We use Pandas chunked reading with pd.read_csv(chunksize=5000) which returns an iterator. Each chunk of 5000 rows is validated independently. Memory usage stays constant regardless of file size. Processing happens in a FastAPI background task so the user gets an immediate response with a job_id and checks status later."

**"Why Parquet as output format?"**
> "Parquet is columnar and compressed — typically 5-10x smaller than CSV. It preserves data types which CSV loses. Any downstream analytics system — data warehouses, ML pipelines, reporting tools — can read Parquet much faster than CSV. It's the industry standard for data pipeline output."

**"Why did you use JWT over sessions?"**
> "JWT is stateless — the server doesn't need to store session data. The token itself contains the user's identity and expiry time, signed with a secret key. This scales horizontally — any server can verify any token without shared session storage. Sessions require a shared database or cache which adds complexity and a single point of failure."

