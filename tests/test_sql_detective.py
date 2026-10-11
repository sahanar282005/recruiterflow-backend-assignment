"""Verification tests for the SQL Detective Challenge queries in sql_detective.sql

Uses the exact RecruiterFlow SQL Detective dataset supplied in the assignment.
"""

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

ASSIGNMENT_DATA_SQL = """
INSERT INTO recruiters VALUES
(1, 'Priya Shah', 'APAC'),
(2, 'Daniel Ortiz', 'NA'),
(3, 'Fatima Al-Sayed', 'EMEA'),
(4, 'Wei Zhang', 'APAC'),
(5, 'Grace Okafor', 'EMEA');

INSERT INTO job_postings VALUES
(1, 'Backend Engineer I', 1, 'Engineering', '2026-01-05', 'open'),
(2, 'Backend Engineer I', 2, 'Engineering', '2026-01-10', 'open'),
(3, 'Data Analyst', 3, 'Data', '2026-01-08', 'closed'),
(4, 'Backend Engineer II', 1, 'Engineering', '2026-02-01', 'open'),
(5, 'DevOps Engineer', 4, 'Infrastructure', '2026-01-20', 'open'),
(6, 'Data Analyst', 5, 'Data', '2026-02-05', 'on_hold'),
(7, 'Backend Engineer I', 2, 'Engineering', '2026-02-15', 'closed');

INSERT INTO applicants VALUES
(1, 'Ananya Rao', 'ananya.rao@mail.com', 'LinkedIn', '2026-01-06'),
(2, 'Ananya Rao', 'Ananya.Rao@mail.com', 'Referral', '2026-02-04'),
(3, 'Ben Turner', 'ben.turner@mail.com', 'Job Board', '2026-01-07'),
(4, 'Chloe Martin', 'chloe.martin@mail.com', NULL, '2026-01-09'),
(5, 'Devansh Patel', 'devansh.patel@mail.com', 'LinkedIn', '2026-01-11'),
(6, 'Elena Popescu', 'elena.popescu@mail.com', 'Referral', '2026-01-12'),
(7, 'Farid Haidari', 'farid.haidari@mail.com', 'Job Board', '2026-01-13'),
(8, 'Grace Lin', 'grace.lin@mail.com', 'LinkedIn', '2026-01-15'),
(9, 'Hassan Malik', 'hassan.malik@mail.com', NULL, '2026-01-16'),
(10, 'Isla Fraser', 'isla.fraser@mail.com', 'Referral', '2026-01-18'),
(11, 'Jonas Weber', 'jonas.weber@mail.com', 'Job Board', '2026-02-10');

INSERT INTO interviews VALUES
(1, 1, 1, 'Screen', '2026-01-10', 'passed'),
(2, 1, 1, 'Technical', '2026-01-15', 'passed'),
(3, 1, 1, 'Final', '2026-01-22', 'passed'),
(4, 2, 4, 'Screen', '2026-02-05', 'passed'),
(5, 3, 1, 'Screen', '2026-01-11', 'passed'),
(6, 3, 1, 'Technical', '2026-01-16', 'failed'),
(7, 3, 3, 'Final', '2026-01-28', 'passed'),
(8, 4, 1, 'Screen', '2026-01-12', 'passed'),
(9, 4, 1, 'Final', '2026-01-24', 'failed'),
(10, 5, 2, 'Screen', '2026-01-14', 'passed'),
(11, 5, 2, 'Technical', '2026-01-19', 'passed'),
(12, 5, 2, 'Final', '2026-01-25', 'passed'),
(13, 6, 2, 'Screen', '2026-01-15', 'passed'),
(14, 6, 2, 'Final', '2026-01-26', 'failed'),
(15, 7, 2, 'Screen', '2026-01-16', 'no_show'),
(16, 8, 4, 'Screen', '2026-02-03', 'passed'),
(17, 8, 4, 'Technical', '2026-02-08', 'passed'),
(18, 8, 4, 'Final', '2026-02-12', 'passed'),
(19, 9, 4, 'Screen', '2026-02-04', 'passed'),
(20, 9, 4, 'Final', '2026-02-14', 'passed'),
(21, 10, 5, 'Screen', '2026-01-22', 'passed'),
(22, 10, 5, 'Technical', '2026-01-28', NULL),
(23, 11, 7, 'Final', '2026-02-20', 'passed'),
(24, 6, 7, 'Final', '2026-02-21', 'failed');
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
    conn.executescript(ASSIGNMENT_DATA_SQL)
    yield conn
    conn.close()


def test_question_1_open_job_postings(db):
    queries = extract_queries()
    q1 = next((q for k, q in queries.items() if "Question 1" in k), None)
    assert q1 is not None

    rows = db.execute(q1).fetchall()
    assert len(rows) == 4

    postings_map = {r["job_posting_id"]: r["recruiter_name"] for r in rows}
    assert postings_map == {
        1: "Priya Shah",
        2: "Daniel Ortiz",
        4: "Priya Shah",
        5: "Wei Zhang",
    }
    for r in rows:
        assert r["status"] == "open"


def test_question_2_final_stage_counts(db):
    queries = extract_queries()
    q2 = next((q for k, q in queries.items() if "Question 2" in k), None)
    assert q2 is not None

    rows = db.execute(q2).fetchall()
    job_counts = {r["job_posting_id"]: r["final_stage_applicants_count"] for r in rows}
    assert job_counts == {
        1: 2,
        2: 2,
        3: 1,
        4: 2,
        5: 0,
        6: 0,
        7: 2,
    }


def test_question_3_duplicate_person_and_multiple_applications(db):
    queries = extract_queries()
    q3 = next((q for k, q in queries.items() if "Question 3" in k), None)
    assert q3 is not None

    rows = db.execute(q3).fetchall()
    assert len(rows) == 3

    names = {r["applicant_name"] for r in rows}
    assert names == {"Ananya Rao", "Ben Turner", "Elena Popescu"}

    emails = {r["normalized_email"] for r in rows}
    assert emails == {
        "ananya.rao@mail.com",
        "ben.turner@mail.com",
        "elena.popescu@mail.com",
    }

    for r in rows:
        assert r["distinct_job_postings_count"] > 1


def test_question_4_recruiter_conversion_rate(db):
    queries = extract_queries()
    q4 = next((q for k, q in queries.items() if "Question 4" in k), None)
    assert q4 is not None

    rows = db.execute(q4).fetchall()
    assert len(rows) == 2

    results = {r["recruiter_name"]: r for r in rows}
    assert set(results.keys()) == {"Priya Shah", "Daniel Ortiz"}

    # Priya Shah: 3 passed / 4 Final interviews -> 0.75
    assert results["Priya Shah"]["total_final_interviews"] == 4
    assert results["Priya Shah"]["passed_final_interviews"] == 3
    assert results["Priya Shah"]["conversion_rate"] == 0.75

    # Daniel Ortiz: 2 passed / 4 Final interviews -> 0.50
    assert results["Daniel Ortiz"]["total_final_interviews"] == 4
    assert results["Daniel Ortiz"]["passed_final_interviews"] == 2
    assert results["Daniel Ortiz"]["conversion_rate"] == 0.50


def test_question_5_top_recruiter_per_department(db):
    queries = extract_queries()
    q5 = next((q for k, q in queries.items() if "Question 5" in k), None)
    assert q5 is not None

    rows = db.execute(q5).fetchall()
    placements = {
        (row["department"], row["recruiter_name"]): row["successful_placements"]
        for row in rows
    }
    assert placements == {
        ("Engineering", "Priya Shah"): 3,
        ("Data", "Fatima Al-Sayed"): 1,
        ("Infrastructure", "Wei Zhang"): 0,
    }

    db.execute(
        "INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?);",
        (25, 1, 1, "Final", "2026-01-23", "passed"),
    )
    rows_with_duplicate = db.execute(q5).fetchall()
    placements_with_duplicate = {
        (row["department"], row["recruiter_name"]): row["successful_placements"]
        for row in rows_with_duplicate
    }
    assert placements_with_duplicate[("Engineering", "Priya Shah")] == 3

    db.execute(
        "INSERT INTO applicants VALUES (?, ?, ?, ?, ?);",
        (12, "Test Applicant", "test@example.com", None, "2026-02-22"),
    )
    db.execute(
        "INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?);",
        (26, 12, 7, "Final", "2026-02-22", "passed"),
    )
    rows_with_tie = db.execute(q5).fetchall()
    engineering_tied_placements = {
        (row["recruiter_name"], row["successful_placements"])
        for row in rows_with_tie
        if row["department"] == "Engineering"
    }
    assert engineering_tied_placements == {
        ("Priya Shah", 3),
        ("Daniel Ortiz", 3),
    }
