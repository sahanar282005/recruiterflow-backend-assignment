"""Verification tests for the SQL Detective Challenge queries in sql_detective.sql."""

import os
import re
import sqlite3
import pytest

SQL_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql_detective.sql"
)

SCHEMA_SQL = """
CREATE TABLE recruiters (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(50)
);

CREATE TABLE job_postings (
    id INT PRIMARY KEY,
    title VARCHAR(100),
    recruiter_id INT,
    department VARCHAR(50),
    opened_date DATE,
    status VARCHAR(20)
);

CREATE TABLE applicants (
    id INT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100),
    source VARCHAR(50),
    applied_date DATE
);

CREATE TABLE interviews (
    id INT PRIMARY KEY,
    applicant_id INT,
    job_posting_id INT,
    stage VARCHAR(20),
    scheduled_date DATE,
    outcome VARCHAR(20)
);
"""

SAMPLE_DATA_SQL = """
-- Recruiters
INSERT INTO recruiters (id, name, region) VALUES
(1, 'Sarah Connor', 'North America'),
(2, 'James Bond', 'Europe'),
(3, 'Diana Prince', 'North America');

-- Job Postings
INSERT INTO job_postings (id, title, recruiter_id, department, opened_date, status) VALUES
(101, 'Senior Backend Engineer', 1, 'Engineering', '2026-01-10', 'open'),
(102, 'DevOps Architect', 1, 'Engineering', '2026-01-15', 'open'),
(103, 'Product Manager', 2, 'Product', '2026-02-01', 'closed'),
(104, 'Data Analyst', 3, 'Data', '2026-02-10', 'open');

-- Applicants (Notice Ananya Rao is listed twice with different email casing)
INSERT INTO applicants (id, full_name, email, source, applied_date) VALUES
(1, 'Ananya Rao', 'ananya.rao@example.com', 'LinkedIn', '2026-01-11'),
(2, 'Ananya Rao', 'Ananya.Rao@example.com', 'Referral', '2026-01-16'),
(3, 'Bruce Wayne', 'bruce.wayne@wayne.com', 'Direct', '2026-01-12'),
(4, 'Clark Kent', 'clark.kent@dailyplanet.com', 'Job Board', '2026-01-14'),
(5, 'Barry Allen', 'barry.allen@starlabs.com', 'Direct', '2026-02-05');

-- Interviews
-- Job 101: Ananya (id 1) Final passed; Bruce (id 3) Final failed; Bruce duplicate interview Final failed
-- Job 102: Ananya (id 2) Final passed; Clark (id 4) Technical passed (not Final)
-- Job 103: Barry (id 5) Final passed
-- Job 104: Zero Final-stage interviews
INSERT INTO interviews (id, applicant_id, job_posting_id, stage, scheduled_date, outcome) VALUES
(1, 1, 101, 'Final', '2026-01-20', 'passed'),
(2, 3, 101, 'Final', '2026-01-21', 'failed'),
(3, 3, 101, 'Final', '2026-01-22', 'failed'), -- Duplicate final interview for same applicant & job
(4, 2, 102, 'Final', '2026-01-25', 'passed'),
(5, 4, 102, 'Technical', '2026-01-18', 'passed'), -- Non-Final stage
(6, 1, 101, 'Screening', '2026-01-12', 'passed'),
(7, 5, 103, 'Final', '2026-02-15', 'passed'),
-- Additional interviews for recruiter 1 to reach >= 3 final interviews:
(8, 4, 101, 'Final', '2026-01-28', 'passed');
"""


def extract_queries():
    """Extract individual queries from sql_detective.sql by question comment."""
    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    queries = {}
    pattern = r"--\s*(Question\s*\d+(?:\s*\(Bonus\))?)(.*?)(?=(?:--\s*Question\s*\d+)|$)"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    for q_label, q_body in matches:
        clean_label = q_label.strip()
        # Clean comment lines out to get just the query
        query_lines = [
            line for line in q_body.splitlines()
            if not line.strip().startswith("--") and line.strip()
        ]
        query = "\n".join(query_lines).strip()
        queries[clean_label] = query

    return queries


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.executescript(SAMPLE_DATA_SQL)
    yield conn
    conn.close()


def test_question_1_open_job_postings(db):
    queries = extract_queries()
    q1 = next((q for k, q in queries.items() if "Question 1" in k), None)
    assert q1 is not None

    rows = db.execute(q1).fetchall()
    # In sample data, job 101, 102, 104 are open; 103 is closed
    open_ids = [r["job_posting_id"] for r in rows]
    assert 101 in open_ids
    assert 102 in open_ids
    assert 104 in open_ids
    assert 103 not in open_ids

    # Recruiter name joined correctly
    job_101 = next(r for r in rows if r["job_posting_id"] == 101)
    assert job_101["recruiter_name"] == "Sarah Connor"


def test_question_2_final_stage_counts(db):
    queries = extract_queries()
    q2 = next((q for k, q in queries.items() if "Question 2" in k), None)
    assert q2 is not None

    rows = db.execute(q2).fetchall()
    # Must include all 4 jobs (even 104 with 0)
    job_counts = {r["job_posting_id"]: r["final_stage_applicants_count"] for r in rows}
    assert len(job_counts) == 4
    assert job_counts[104] == 0  # 0 final stage applicants preserved via outer join
    assert job_counts[102] == 1  # only Ananya (applicant 2) has Final; Clark has Technical
    assert job_counts[101] == 3  # applicants 1, 3, and 4


def test_question_3_duplicate_person_and_multiple_applications(db):
    queries = extract_queries()
    q3 = next((q for k, q in queries.items() if "Question 3" in k), None)
    assert q3 is not None

    rows = db.execute(q3).fetchall()
    # Ananya Rao effectively applied to jobs 101 and 102 via interviews
    emails = [r["normalized_email"] for r in rows]
    assert "ananya.rao@example.com" in emails

    ananya = next(r for r in rows if r["normalized_email"] == "ananya.rao@example.com")
    assert ananya["distinct_job_postings_count"] == 2
    # Bruce Wayne only applied to job 101, so should NOT be in the result
    assert "bruce.wayne@wayne.com" not in emails


def test_question_4_recruiter_conversion_rate(db):
    queries = extract_queries()
    q4 = next((q for k, q in queries.items() if "Question 4" in k), None)
    assert q4 is not None

    rows = db.execute(q4).fetchall()
    # Recruiter 1 (Sarah Connor) owns jobs 101 & 102.
    # Total Final-stage interviews for recruiter 1:
    # id 1 (passed), id 2 (failed), id 3 (failed), id 4 (passed), id 8 (passed) -> total 5 interviews, 3 passed.
    # Rate: 3 / 5 = 0.60
    # Recruiter 2 (James Bond) has only 1 Final interview (id 7) -> excluded by HAVING COUNT >= 3
    # Recruiter 3 has 0 -> excluded
    recruiter_ids = [r["recruiter_id"] for r in rows]
    assert recruiter_ids == [1]

    r1 = rows[0]
    assert r1["recruiter_name"] == "Sarah Connor"
    assert r1["total_final_interviews"] == 5
    assert r1["passed_final_interviews"] == 3
    assert r1["conversion_rate"] == 0.6


def test_question_5_top_recruiter_per_department(db):
    queries = extract_queries()
    q5 = next((q for k, q in queries.items() if "Question 5" in k), None)
    assert q5 is not None

    rows = db.execute(q5).fetchall()
    dept_map = {r["department"]: r["recruiter_name"] for r in rows}
    # Engineering: Sarah Connor (3 successful placements)
    # Product: James Bond (1 successful placement)
    assert dept_map["Engineering"] == "Sarah Connor"
    assert dept_map["Product"] == "James Bond"
