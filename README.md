# RecruiterFlow — Build-a-Recruiter-Bot Backend

A production-ready, lightweight backend implementing the **RecruiterFlow Engineering — Build-a-Recruiter-Bot** assignment.

This project delivers:
1. **Part 1 — Recruiter Bot**: A FastAPI service powered by raw, handwritten SQLite SQL that implements a transparent, two-way candidate-job matching engine with 60/30/10 weighted scoring and human-readable explanations.
2. **Part 2 — SQL Detective Challenge**: Handwritten analytical SQL queries solving complex hiring-ops data challenges involving deduplication, conversion rates, and window functions.

---

## 1. Technology Stack

* **Language**: Python 3.11+
* **Web Framework**: FastAPI (0.111+)
* **ASGI Server**: Uvicorn (0.30+)
* **Database**: SQLite 3 (via Python standard library `sqlite3`)
* **SQL**: 100% handwritten raw SQL and DDL (Zero ORM, zero query builders)
* **Testing**: Pytest & HTTPX (TestClient)

---

## 2. Project Structure

```
recruiter-bot/
├── app/
│   ├── __init__.py          # Application package marker
│   ├── database.py         # SQLite connection manager & schema initializer
│   ├── schema.sql           # Handwritten SQL DDL for candidates and jobs
│   ├── seed.py              # Deterministic, repeatable ingestion of seed data
│   ├── matching.py          # 60/30/10 weighted matching engine & tie-breaking logic
│   └── main.py              # FastAPI application & REST endpoints
├── tests/
│   ├── test_api.py          # Integration tests for API routes, 404s, and seed idempotency
│   ├── test_matching.py     # Unit tests for scoring weights, normalization, and edge cases
│   └── test_sql_detective.py# Automated tests verifying all 5 SQL detective queries
├── sql_detective.sql        # Executable SQL file with solutions for Questions 1–5
├── requirements.txt         # Application dependencies
├── README.md                # Comprehensive project documentation
└── .gitignore               # Excludes virtual environments, database files, and caches
```

---

## 3. Database Schema Design & Rationale

The database uses handwritten SQLite DDL defined in [`app/schema.sql`](file:///Users/sagar/recruiter-bot/app/schema.sql).

### Normalized Tables
* **`candidates`**: Core candidate attributes (`id`, `name`, `experience`, `availability`, `quirk`).
* **`candidate_skills`**: Relational junction table mapping `candidate_id` to `skill` (composite primary key, foreign key with `ON DELETE CASCADE`).
* **`candidate_traits`**: Relational junction table mapping `candidate_id` to `trait` (composite primary key, foreign key with `ON DELETE CASCADE`).
* **`jobs`**: Core job attributes (`id`, `title`, `min_experience`, `tagline`).
* **`job_required_skills`**: Relational junction table mapping `job_id` to `skill` (composite primary key, foreign key with `ON DELETE CASCADE`).
* **`job_culture_keywords`**: Relational junction table mapping `job_id` to `keyword` (composite primary key, foreign key with `ON DELETE CASCADE`).

```sql
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    experience INTEGER NOT NULL CHECK (experience >= 0),
    availability TEXT NOT NULL,
    quirk TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (candidate_id, skill),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS candidate_traits (
    candidate_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    PRIMARY KEY (candidate_id, trait),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    tagline TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_required_skills (
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_culture_keywords (
    job_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    PRIMARY KEY (job_id, keyword),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
```

### Schema Rationale
* **Core Attributes Separation**: Candidate and job core attributes remain in their own tables (`candidates`, `jobs`).
* **Normalized Relationship Tables**: Multi-valued skills, traits, required skills, and culture keywords are represented using normalized relationship tables.
* **Relational Querying & Indexing**: This avoids JSON-in-TEXT storage, maintains standard relational normalization, and enables direct relational querying and indexing via foreign key references.
* **Dynamic Match Computation**: Matches are computed dynamically rather than persisted in a `matches` table. This avoids stale cache invalidation issues when candidate experience or job requirements change, ensuring guaranteed real-time consistency.

---

## 4. Ingestion Procedure

Deterministic data ingestion is implemented in [`app/seed.py`](file:///Users/sagar/recruiter-bot/app/seed.py):
* All **15 candidates** and all **6 jobs** are seeded with their exact supplied attributes.
* Ingestion is completely **idempotent**:
  - `candidates` uses `ON CONFLICT(name) DO UPDATE SET ...`
  - `jobs` uses `ON CONFLICT(title) DO UPDATE SET ...`
* Running the seed script multiple times will never duplicate rows or produce duplicate IDs.
* When the FastAPI application boots, the application lifecycle automatically initializes the schema and seeds the database if empty.

---

## 5. Quickstart & Installation

### Step 1: Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Seed the Database
```bash
python -m app.seed
```
*Expected output:*
```
Database seeded successfully: 15 candidates, 6 jobs.
```

### Step 4: Run the Test Suite
```bash
pytest -v
```
All 16 unit, integration, and SQL detective tests will run and pass.

### Step 5: Start the API Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at:
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* OpenAPI JSON: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 6. Matching Algorithm Specification

The matching algorithm in [`app/matching.py`](file:///Users/sagar/recruiter-bot/app/matching.py) is deterministic, transparent, and symmetric in forward (`Job -> Candidates`) and reverse (`Candidate -> Jobs`) directions.

### Score Weights (0 to 100 Points)
1. **Skill Overlap (60 points)**:
   $$\text{skill\_score} = \left(\frac{\text{matching required skills}}{\text{total required skills}}\right) \times 60$$
   * Tokens are normalized (lowercase and trimmed whitespace).

2. **Experience Fit (30 points)**:
   * If $\text{candidate\_experience} \ge \text{minimum\_experience}$:
     $$\text{experience\_score} = 30$$
   * If $\text{candidate\_experience} < \text{minimum\_experience}$:
     $$\text{experience\_score} = 30 \times \left(\frac{\text{candidate\_experience}}{\text{minimum\_experience}}\right)$$
   * If $\text{minimum\_experience} = 0$: $\text{experience\_score} = 30$.
   * This rewards meeting the baseline without awarding unlimited extra credit for seniority.

3. **Culture / Trait Alignment (10 points)**:
   $$\text{culture\_score} = \left(\frac{\text{matching candidate traits and culture keywords}}{\text{total culture keywords}}\right) \times 10$$
   * Normalized string comparisons.

4. **Final Score**:
   $$\text{final\_score} = \text{round}(\text{skill\_score} + \text{experience\_score} + \text{culture\_score}, 2)$$

### Deterministic Tie-Breaking Rules
If two records produce identical final scores, ties are broken deterministically in this order:
1. Higher skill overlap count (descending)
2. Alphabetical candidate name / job title (case-insensitive ascending)
3. Stable record ID (ascending)

### Match Reasons
Every match generates a human-readable explanation derived directly from the underlying score components:
* `Matches 3 of 3 required skills; experience meets the 3-year minimum; culture alignment 1 of 2.`
* `Matches 1 of 2 required skills; experience is below the 5-year minimum; culture alignment 2 of 2.`

---

## 7. API Endpoints

### 1. `GET /jobs/{id}/matches`
Returns all 15 candidates ranked for the specified job ID.

#### `curl` Request:
```bash
curl -X GET http://127.0.0.1:8000/jobs/1/matches
```

#### Sample Response (`200 OK`):
```json
{
  "job_id": 1,
  "job_title": "Backend Detective",
  "matches": [
    {
      "candidate_id": 1,
      "candidate_name": "Sherlock H.",
      "score": 95.0,
      "reason": "Matches 3 of 3 required skills; experience meets the 3-year minimum; culture alignment 1 of 2."
    },
    {
      "candidate_id": 9,
      "candidate_name": "Sheldon C.",
      "score": 50.0,
      "reason": "Matches 1 of 3 required skills; experience meets the 3-year minimum; culture alignment 0 of 2."
    },
    {
      "candidate_id": 15,
      "candidate_name": "Dwight S.",
      "score": 30.0,
      "reason": "Matches 0 of 3 required skills; experience meets the 3-year minimum; culture alignment 0 of 2."
    }
  ]
}
```

---

### 2. `GET /candidates/{id}/matches`
Returns all 6 jobs ranked for the specified candidate ID.

#### `curl` Request:
```bash
curl -X GET http://127.0.0.1:8000/candidates/1/matches
```

#### Sample Response (`200 OK`):
```json
{
  "candidate_id": 1,
  "candidate_name": "Sherlock H.",
  "matches": [
    {
      "job_id": 1,
      "job_title": "Backend Detective",
      "score": 95.0,
      "reason": "Matches 3 of 3 required skills; experience meets the 3-year minimum; culture alignment 1 of 2."
    },
    {
      "job_id": 3,
      "job_title": "Developer Relations Lead",
      "score": 30.0,
      "reason": "Matches 0 of 2 required skills; experience meets the 2-year minimum; culture alignment 0 of 2."
    },
    {
      "job_id": 4,
      "job_title": "Engineering Manager, Chaos Team",
      "score": 30.0,
      "reason": "Matches 0 of 3 required skills; experience meets the 5-year minimum; culture alignment 0 of 2."
    }
  ]
}
```

---

### 3. Nonexistent ID Handling (`404 Not Found`)
When requesting an ID that does not exist in the database, the server returns an HTTP 404 response:

#### Request:
```bash
curl -X GET http://127.0.0.1:8000/jobs/999/matches
```

#### Response:
```json
{
  "detail": "Job with ID 999 not found"
}
```

#### Request:
```bash
curl -X GET http://127.0.0.1:8000/candidates/999/matches
```

#### Response:
```json
{
  "detail": "Candidate with ID 999 not found"
}
```

---

### 4. Health Check
`GET /health` returns `{"status": "ok"}` for service verification.

---

## 8. Part 2 — SQL Detective Challenge

The file [`sql_detective.sql`](file:///Users/sagar/recruiter-bot/sql_detective.sql) contains five handwritten SQL queries addressing analytical recruitment questions against the hiring-ops database:

1. **Question 1**: Open job postings and the names of the recruiters who own them.
2. **Question 2**: Count of distinct applicants reaching the `Final` stage per job posting, using a `LEFT JOIN` to preserve postings with zero Final-stage applicants.
3. **Question 3**: Identifying applicants who applied to more than one distinct job posting, handling casing anomalies (such as duplicate Ananya Rao records with different email capitalization) via `LOWER(email)` and counting distinct `job_posting_id`s through interviews.
4. **Question 4**: Recruiter Final-stage conversion rate (`passed ÷ total Final-stage interviews`), filtered to recruiters with at least 3 Final-stage interviews and protected against division by zero using `NULLIF`.
5. **Question 5 (Bonus)**: Recruiter with the most successful placements (`stage = 'Final' AND outcome = 'passed'`) per department using a `DENSE_RANK()` window function.

### Running the SQL Queries
To execute against a SQLite database populated with the hiring-ops schema:
```bash
sqlite3 hiring_ops.db < sql_detective.sql
```
Or execute the automated test suite verifying all 5 queries:
```bash
pytest tests/test_sql_detective.py -v
```

---

## 9. Assumptions and Trade-offs

1. **Database Access**: Direct standard library `sqlite3` was used with raw parameterized SQL (`?` placeholders) to comply strictly with the no-ORM, handwritten SQL constraint.
2. **Candidate-Job Matches Storage**: Computed dynamically on request rather than saved in a permanent `matches` table. This prevents data drift when candidates or job requirements change and eliminates unnecessary database writes.
3. **Multivalued Attributes**: Represented using normalized relationship tables (`candidate_skills`, `candidate_traits`, `job_required_skills`, `job_culture_keywords`) with foreign keys and compound primary keys, providing clean relational normalization without JSON-in-TEXT storage.
4. **Tie-Breaking Rule**: When two candidates or jobs share the exact same score, ties are broken first by higher skill overlap count, second by case-insensitive name/title ascending, and third by record ID ascending.
5. **Window Function Ties in Question 5**: `DENSE_RANK()` was chosen over `ROW_NUMBER()` so that in the event of a tie for top placements in a department, all tied recruiters are fairly included rather than arbitrarily excluding one.
