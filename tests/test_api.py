"""Integration tests for FastAPI endpoints and database seeding."""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.seed import seed_database
from app.database import get_db_connection


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database is seeded before running tests."""
    c_count, j_count = seed_database()
    assert c_count == 15
    assert j_count == 6


@pytest.fixture
def client():
    return TestClient(app)


def test_seed_idempotency():
    """Verify that running seed multiple times does not create duplicate records."""
    c_count1, j_count1 = seed_database()
    c_count2, j_count2 = seed_database()
    assert c_count1 == 15
    assert c_count2 == 15
    assert j_count1 == 6
    assert j_count2 == 6

    conn = get_db_connection()
    try:
        cand_count = conn.execute("SELECT COUNT(*) FROM candidates;").fetchone()[0]
        job_count = conn.execute("SELECT COUNT(*) FROM jobs;").fetchone()[0]
        assert cand_count == 15
        assert job_count == 6
    finally:
        conn.close()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_job_matches_valid(client):
    # Job 1 is Backend Detective (requires deduction, pattern-recognition, forensics; min_exp: 3; culture: analytical, autonomous)
    response = client.get("/jobs/1/matches")
    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == 1
    assert data["job_title"] == "Backend Detective"
    matches = data["matches"]
    assert len(matches) == 15

    # Sherlock H. has all 3 skills, 8 yrs exp (>= 3), and "analytical" trait (1 of 2 culture)
    # Expected score: 60 + 30 + (1/2 * 10 = 5) = 95.0
    top_match = matches[0]
    assert top_match["candidate_name"] == "Sherlock H."
    assert top_match["score"] == 95.0
    assert "Matches 3 of 3 required skills" in top_match["reason"]
    assert "experience meets the 3-year minimum" in top_match["reason"]
    assert "culture alignment 1 of 2" in top_match["reason"]

    # Verify descending score order
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_get_candidate_matches_valid(client):
    # Candidate 1 is Sherlock H.
    response = client.get("/candidates/1/matches")
    assert response.status_code == 200
    data = response.json()

    assert data["candidate_id"] == 1
    assert data["candidate_name"] == "Sherlock H."
    matches = data["matches"]
    assert len(matches) == 6

    # Backend Detective should be top job for Sherlock H. with 95.0
    top_match = matches[0]
    assert top_match["job_title"] == "Backend Detective"
    assert top_match["score"] == 95.0

    # Verify descending score order
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_get_job_matches_not_found(client):
    response = client.get("/jobs/999/matches")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_candidate_matches_not_found(client):
    response = client.get("/candidates/999/matches")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
