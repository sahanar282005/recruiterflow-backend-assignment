"""FastAPI backend application for RecruiterFlow Bot."""

import json
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException, status
from app.database import get_db_connection
from app.seed import seed_database
from app.matching import rank_candidates_for_job, rank_jobs_for_candidate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database is initialized and seeded on application startup."""
    seed_database()
    yield


app = FastAPI(
    title="RecruiterFlow Bot API",
    description="Deterministic candidate-job matching engine using handwritten SQLite SQL.",
    version="1.0.0",
    lifespan=lifespan,
)


def _row_to_candidate(row: Any) -> dict[str, Any]:
    """Convert sqlite3.Row to candidate dictionary with deserialized JSON fields."""
    return {
        "id": row["id"],
        "name": row["name"],
        "skills": json.loads(row["skills"]),
        "experience": row["experience"],
        "availability": row["availability"],
        "traits": json.loads(row["traits"]),
        "quirk": row["quirk"],
    }


def _row_to_job(row: Any) -> dict[str, Any]:
    """Convert sqlite3.Row to job dictionary with deserialized JSON fields."""
    return {
        "id": row["id"],
        "title": row["title"],
        "required_skills": json.loads(row["required_skills"]),
        "min_experience": row["min_experience"],
        "culture_keywords": json.loads(row["culture_keywords"]),
        "tagline": row["tagline"],
    }


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """Minimal health verification endpoint."""
    return {"status": "ok"}


@app.get("/jobs/{id}/matches", status_code=status.HTTP_200_OK, tags=["Matching"])
def get_job_matches(id: int):
    """Return candidates ranked for the specified job."""
    conn = get_db_connection()
    try:
        # Parameterized query to fetch job by ID
        job_row = conn.execute(
            """
            SELECT id, title, required_skills, min_experience, culture_keywords, tagline
            FROM jobs
            WHERE id = ?;
            """,
            (id,),
        ).fetchone()

        if not job_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {id} not found",
            )

        job = _row_to_job(job_row)

        # Parameterized query to fetch all candidates
        candidate_rows = conn.execute(
            """
            SELECT id, name, skills, experience, availability, traits, quirk
            FROM candidates;
            """
        ).fetchall()

        candidates = [_row_to_candidate(r) for r in candidate_rows]
        matches = rank_candidates_for_job(job, candidates)

        return {
            "job_id": job["id"],
            "job_title": job["title"],
            "matches": matches,
        }
    finally:
        conn.close()


@app.get("/candidates/{id}/matches", status_code=status.HTTP_200_OK, tags=["Matching"])
def get_candidate_matches(id: int):
    """Return jobs ranked for the specified candidate."""
    conn = get_db_connection()
    try:
        # Parameterized query to fetch candidate by ID
        candidate_row = conn.execute(
            """
            SELECT id, name, skills, experience, availability, traits, quirk
            FROM candidates
            WHERE id = ?;
            """,
            (id,),
        ).fetchone()

        if not candidate_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {id} not found",
            )

        candidate = _row_to_candidate(candidate_row)

        # Parameterized query to fetch all jobs
        job_rows = conn.execute(
            """
            SELECT id, title, required_skills, min_experience, culture_keywords, tagline
            FROM jobs;
            """
        ).fetchall()

        jobs = [_row_to_job(r) for r in job_rows]
        matches = rank_jobs_for_candidate(candidate, jobs)

        return {
            "candidate_id": candidate["id"],
            "candidate_name": candidate["name"],
            "matches": matches,
        }
    finally:
        conn.close()
