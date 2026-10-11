# Build-a-Recruiter-Bot

A backend service for the RecruiterFlow Backend Developer Intern assignment. It stores the assignment's fictional candidate profiles and job openings in SQLite, calculates candidate-job compatibility, and returns ranked matches through REST APIs. The separate SQL Detective solution answers five hiring-operations questions against the assignment's supplied schema and data.

## Features

- Loads 15 fictional candidates and 6 jobs from a repeatable seed script.
- Stores candidates, jobs, and their multi-valued attributes in relational tables.
- Uses handwritten SQL through Python's `sqlite3` driver; no ORM or query builder is used.
- Ranks candidates for a job and jobs for a candidate, with a score and explanation for each result.
- Includes the SQL Detective answers, automated matching and SQL tests, and FastAPI's generated OpenAPI documentation.

## Technology Stack

| Technology | Use |
|---|---|
| Python 3.10+ | Application runtime |
| FastAPI | HTTP API and OpenAPI documentation |
| Uvicorn | ASGI server |
| SQLite / Python `sqlite3` | Relational storage and handwritten SQL |
| Pytest | Unit and integration tests |
| HTTPX | FastAPI `TestClient` dependency |

The Python 3.10 minimum follows from the union type syntax used in the source. Dependency minimums are listed in [`requirements.txt`](requirements.txt).

## Project Structure

```text
.
├── app/
│   ├── __init__.py
│   ├── database.py          # SQLite connection and schema initialization
│   ├── main.py              # FastAPI application, SQL reads, and API routes
│   ├── matching.py          # Scoring, explanations, and ranking
│   ├── schema.sql           # Handwritten application schema and indexes
│   └── seed.py              # Fictional candidate and job data; seed routine
├── tests/
│   ├── test_api.py          # API behavior and seed idempotency
│   ├── test_matching.py     # Scoring and ranking behavior
│   └── test_sql_detective.py # SQL answers run on in-memory SQLite data
├── sql_detective.sql        # SQL Detective answers, Questions 1-5
├── requirements.txt
├── .gitignore
└── README.md
```

`recruiter.db` is a local runtime database ignored by Git; it is created when the schema is initialized. Virtual environments and Python/test caches are also ignored.

## Prerequisites

- Python 3.10 or newer.
- Git to clone the repository.
- No separate database server is required. SQLite is accessed through Python's standard library.

## Installation and Setup

Clone the repository (replace the placeholder with the repository URL):

```text
git clone https://github.com/sahanar282005/recruiterflow-backend-assignment.git
cd recruiterflow-backend-assignment
```

Create and activate a virtual environment.

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies and seed the database:

```bash
python -m pip install -r requirements.txt
python -m app.seed
```

The seed command creates the schema if needed, then inserts or updates the supplied candidate and job records and refreshes their associated skills, traits, and keywords. It prints the candidate and job counts on success.

Start the API:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The default database is `recruiter.db` in the repository root, regardless of the working directory used to launch the app. Set `DATABASE_PATH` to use another SQLite file. For example, in PowerShell use `$env:DATABASE_PATH = "C:\path\to\recruiter.db"`; in macOS/Linux use `export DATABASE_PATH="/path/to/recruiter.db"`. The app initializes the schema and runs the seed routine when it starts, so startup updates the supplied records as well.

The local API address is `http://127.0.0.1:8000`. FastAPI serves Swagger UI at [`/docs`](http://127.0.0.1:8000/docs) and the OpenAPI document at [`/openapi.json`](http://127.0.0.1:8000/openapi.json).

## Database Design and SQL

The handwritten DDL in [`app/schema.sql`](app/schema.sql) defines:

| Table | Contents |
|---|---|
| `candidates` | Candidate name, experience, availability, and quirk |
| `candidate_skills` | One skill per candidate relationship row |
| `candidate_traits` | One trait per candidate relationship row |
| `jobs` | Job title, minimum experience, and tagline |
| `job_required_skills` | One required skill per job relationship row |
| `job_culture_keywords` | One culture keyword per job relationship row |

Candidate and job IDs are integer primary keys. Names and titles are unique; experience values have non-negative `CHECK` constraints. Relationship tables use composite primary keys and foreign keys with `ON DELETE CASCADE`. The schema also defines indexes for names, titles, and relationship-table parent IDs. Connections enable SQLite foreign-key enforcement.

Skills, traits, and keywords are stored in relationship tables rather than packed into text fields, allowing relational reads and enforcing uniqueness per parent. Database access throughout the application is handwritten SQL using `sqlite3`; values are passed using bound parameters. No ORM or query builder is used. Match results are computed when requested and are not stored in a match table.

## Data Ingestion

[`app/seed.py`](app/seed.py) contains the assignment's 15 candidates and 6 jobs, including skills, experience, availability, traits, quirks, required skills, culture keywords, and taglines. Run it with `python -m app.seed`. Existing rows with the same candidate name or job title are updated; their related skill, trait, and keyword rows are replaced from the seed data. Seeding the same supplied data repeatedly does not create duplicates. The script does not delete unrelated extra candidate or job rows.

## Matching Algorithm

The matching logic in [`app/matching.py`](app/matching.py) normalizes skill and trait/keyword tokens by trimming whitespace and converting to lowercase, then compares unique token sets. Scores use a 0-100 point scale:

| Component | Weight | Calculation |
|---|---:|---|
| Required skill overlap | 60 points | `60 * matching required skills / total unique required skills` |
| Experience fit | 30 points | 30 when experience meets the minimum; otherwise `30 * candidate experience / minimum experience` |
| Culture/trait alignment | 10 points | `10 * matching culture keywords / total unique culture keywords` |

Each component is zero when its corresponding requirement list is empty, except experience: a minimum of zero receives all 30 experience points. The total is the sum of the components rounded to two decimal places. With the supplied non-negative data, the resulting score ranges from 0 to 100.

Results are sorted by total score descending, skill-overlap count descending, then candidate name or job title case-insensitively ascending, and finally record ID ascending. This makes equal scores deterministic while preferring stronger skill overlap before alphabetical ordering.

Each explanation is constructed from the same computed values: matching versus total required skills, whether experience meets the minimum, and matching versus total culture keywords. Availability, quirks, and job taglines are stored but do not affect scoring. Culture matching is exact after lowercase/whitespace normalization; there is no semantic or fuzzy matching. These choices make the ranking understandable and deterministic, while leaving more advanced matching factors for future work.

## API Reference

Both routes return all matching records, ordered by score. `score` is the calculated 0-100 compatibility score; `reason` summarizes the skill, experience, and culture components.

### `GET /jobs/{id}/matches`

Returns candidate rankings for a job. `id` is the integer job ID. A missing job returns `404` with a `detail` message.

```bash
curl http://127.0.0.1:8000/jobs/1/matches
```

Representative response (the `matches` array is shortened here; the endpoint returns all candidates):

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
    }
  ]
}
```

### `GET /candidates/{id}/matches`

Returns job rankings for a candidate. `id` is the integer candidate ID. A missing candidate returns `404` with a `detail` message.

```bash
curl http://127.0.0.1:8000/candidates/1/matches
```

Representative response (the `matches` array is shortened here; the endpoint returns all jobs):

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
    }
  ]
}
```

For example, requesting `/jobs/999/matches` returns `{"detail":"Job with ID 999 not found"}` with status `404`; the candidate route uses the corresponding candidate-specific message. `GET /health` returns `{"status":"ok"}`.

## SQL Detective Challenge

[`sql_detective.sql`](sql_detective.sql) contains the assignment's five SQL answers for its separate hiring-operations schema:

1. Open job postings and their recruiters.
2. Final-stage applicant counts for each posting, including zero-count postings.
3. People associated with more than one posting, normalizing email casing and counting distinct postings.
4. Recruiter Final-stage conversion rates, limited to recruiters with at least three Final interviews.
5. **Bonus:** Recruiter(s) with the most successful Final-stage placements per department, including departments with zero successful placements and preserving ties.

The queries use SQLite-compatible SQL. Question 5 uses a window function supported by SQLite 3.25.0 and later. The SQL test suite creates the assignment schema and data in an in-memory database; the SQL file itself expects the hiring-operations tables to exist already.

## Testing

Run the test suite with:

```bash
python -m pytest -v
```

The suite contains matching unit tests, API/seed integration tests, and SQL Detective tests. The SQL tests use in-memory SQLite. **The API test fixture calls `seed_database()` against the default database**, and the seed-idempotency test calls it again. 
Database safety: The API tests use the configured database and may create or update recruiter.db, including replacing seeded relationship rows. Run the full suite with a disposable database, or back up your local database first. The SQL tests use an in-memory database. The current API tests do not automatically isolate themselves from the default database.

## Design Decisions and Trade-offs

- **SQLite and handwritten SQL:** This keeps the assignment self-contained and satisfies its raw-SQL constraint without a database server. The implementation is SQLite-specific and does not provide database migrations.
- **Normalized multi-valued attributes:** Separate skill, trait, and keyword tables avoid delimited text storage and enforce per-parent uniqueness. Reads require additional queries to assemble the API's candidate and job objects.
- **Dynamic, explainable matching:** Scores are computed from current records at request time, avoiding stale stored scores. The fixed weighted formula is easy to explain but does not learn from outcomes or account for availability.
- **Deterministic ranking:** Stable tie-breakers make output order repeatable, at the cost of using alphabetical order as the final preference when score and overlap tie.

## Limitations and Future Improvements

The API currently returns every candidate/job match without pagination. Matching uses exact normalized token equality and does not use availability, quirks, or job taglines. The API tests share the default database rather than an isolated test database. Possible future work includes pagination, broader integration coverage with an isolated database, and evaluating additional matching signals; these are not implemented currently.

## AI Tool Usage

AI tools were used to review the assignment requirements, identify potential issues, debug API tests, and refine the bonus Question 5 SQL query and its tests. The implementation was reviewed and tested, and I take responsibility for understanding the code and explaining the design decisions and trade-offs.

## Assignment Context and Repository

This repository implements RecruiterFlow's **Backend Developer Intern** take-home assignment: the Recruiter Bot backend and the separate SQL Detective Challenge.
