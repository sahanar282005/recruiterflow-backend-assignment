"""FastAPI backend application for RecruiterFlow Bot using normalized relational tables."""

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


def _fetch_candidate_by_id(conn: Any, candidate_id: int) -> dict[str, Any] | None:
    """Fetch a single candidate and their normalized skills/traits using handwritten SQL."""
    cand_row = conn.execute(
        """
        SELECT id, name, experience, availability, quirk
        FROM candidates
        WHERE id = ?;
        """,
        (candidate_id,),
    ).fetchone()

    if not cand_row:
        return None

    skills = [
        r["skill"]
        for r in conn.execute(
            """
            SELECT skill FROM candidate_skills
            WHERE candidate_id = ?
            ORDER BY rowid;
            """,
            (candidate_id,),
        ).fetchall()
    ]

    traits = [
        r["trait"]
        for r in conn.execute(
            """
            SELECT trait FROM candidate_traits
            WHERE candidate_id = ?
            ORDER BY rowid;
            """,
            (candidate_id,),
        ).fetchall()
    ]

    return {
        "id": cand_row["id"],
        "name": cand_row["name"],
        "skills": skills,
        "experience": cand_row["experience"],
        "availability": cand_row["availability"],
        "traits": traits,
        "quirk": cand_row["quirk"],
    }


def _fetch_all_candidates(conn: Any) -> list[dict[str, Any]]:
    """Fetch all candidates and their normalized skills/traits using handwritten SQL."""
    cand_rows = conn.execute(
        """
        SELECT id, name, experience, availability, quirk
        FROM candidates
        ORDER BY id;
        """
    ).fetchall()

    skill_rows = conn.execute(
        """
        SELECT candidate_id, skill
        FROM candidate_skills
        ORDER BY rowid;
        """
    ).fetchall()
    skills_map: dict[int, list[str]] = {}
    for r in skill_rows:
        skills_map.setdefault(r["candidate_id"], []).append(r["skill"])

    trait_rows = conn.execute(
        """
        SELECT candidate_id, trait
        FROM candidate_traits
        ORDER BY rowid;
        """
    ).fetchall()
    traits_map: dict[int, list[str]] = {}
    for r in trait_rows:
        traits_map.setdefault(r["candidate_id"], []).append(r["trait"])

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "skills": skills_map.get(r["id"], []),
            "experience": r["experience"],
            "availability": r["availability"],
            "traits": traits_map.get(r["id"], []),
            "quirk": r["quirk"],
        }
        for r in cand_rows
    ]


def _fetch_job_by_id(conn: Any, job_id: int) -> dict[str, Any] | None:
    """Fetch a single job and its normalized required skills/culture keywords using handwritten SQL."""
    job_row = conn.execute(
        """
        SELECT id, title, min_experience, tagline
        FROM jobs
        WHERE id = ?;
        """,
        (job_id,),
    ).fetchone()

    if not job_row:
        return None

    required_skills = [
        r["skill"]
        for r in conn.execute(
            """
            SELECT skill FROM job_required_skills
            WHERE job_id = ?
            ORDER BY rowid;
            """,
            (job_id,),
        ).fetchall()
    ]

    culture_keywords = [
        r["keyword"]
        for r in conn.execute(
            """
            SELECT keyword FROM job_culture_keywords
            WHERE job_id = ?
            ORDER BY rowid;
            """,
            (job_id,),
        ).fetchall()
    ]

    return {
        "id": job_row["id"],
        "title": job_row["title"],
        "required_skills": required_skills,
        "min_experience": job_row["min_experience"],
        "culture_keywords": culture_keywords,
        "tagline": job_row["tagline"],
    }


def _fetch_all_jobs(conn: Any) -> list[dict[str, Any]]:
    """Fetch all jobs and their normalized required skills/culture keywords using handwritten SQL."""
    job_rows = conn.execute(
        """
        SELECT id, title, min_experience, tagline
        FROM jobs
        ORDER BY id;
        """
    ).fetchall()

    skill_rows = conn.execute(
        """
        SELECT job_id, skill
        FROM job_required_skills
        ORDER BY rowid;
        """
    ).fetchall()
    skills_map: dict[int, list[str]] = {}
    for r in skill_rows:
        skills_map.setdefault(r["job_id"], []).append(r["skill"])

    keyword_rows = conn.execute(
        """
        SELECT job_id, keyword
        FROM job_culture_keywords
        ORDER BY rowid;
        """
    ).fetchall()
    keywords_map: dict[int, list[str]] = {}
    for r in keyword_rows:
        keywords_map.setdefault(r["job_id"], []).append(r["keyword"])

    return [
        {
            "id": r["id"],
            "title": r["title"],
            "required_skills": skills_map.get(r["id"], []),
            "min_experience": r["min_experience"],
            "culture_keywords": keywords_map.get(r["id"], []),
            "tagline": r["tagline"],
        }
        for r in job_rows
    ]


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """Minimal health verification endpoint."""
    return {"status": "ok"}


@app.get("/jobs/{id}/matches", status_code=status.HTTP_200_OK, tags=["Matching"])
def get_job_matches(id: int):
    """Return candidates ranked for the specified job."""
    conn = get_db_connection()
    try:
        job = _fetch_job_by_id(conn, id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {id} not found",
            )

        candidates = _fetch_all_candidates(conn)
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
        candidate = _fetch_candidate_by_id(conn, id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {id} not found",
            )

        jobs = _fetch_all_jobs(conn)
        matches = rank_jobs_for_candidate(candidate, jobs)

        return {
            "candidate_id": candidate["id"],
            "candidate_name": candidate["name"],
            "matches": matches,
        }
    finally:
        conn.close()
