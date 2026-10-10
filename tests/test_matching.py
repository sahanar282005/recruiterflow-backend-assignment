"""Unit tests for the matching algorithm."""

import pytest
from app.matching import calculate_match, rank_candidates_for_job, rank_jobs_for_candidate


def test_perfect_match():
    candidate = {
        "id": 1,
        "name": "Perfect Match",
        "skills": ["python", "sql", "fastapi"],
        "experience": 5,
        "availability": "Immediate",
        "traits": ["analytical", "communicative"],
        "quirk": "Writes clean code.",
    }
    job = {
        "id": 1,
        "title": "Backend Dev",
        "required_skills": ["python", "sql", "fastapi"],
        "min_experience": 3,
        "culture_keywords": ["analytical", "communicative"],
        "tagline": "Join us.",
    }

    result = calculate_match(candidate, job)
    assert result["skill_score"] == 60.0
    assert result["experience_score"] == 30.0
    assert result["culture_score"] == 10.0
    assert result["final_score"] == 100.0
    assert "Matches 3 of 3 required skills" in result["reason"]
    assert "experience meets the 3-year minimum" in result["reason"]
    assert "culture alignment 2 of 2" in result["reason"]


def test_experience_below_minimum():
    candidate = {
        "id": 2,
        "name": "Junior Dev",
        "skills": ["python"],
        "experience": 2,
        "availability": "Immediate",
        "traits": ["curious"],
        "quirk": "Eager to learn.",
    }
    job = {
        "id": 2,
        "title": "Senior Dev",
        "required_skills": ["python", "system-design"],
        "min_experience": 4,
        "culture_keywords": ["innovative"],
        "tagline": "Senior role.",
    }

    result = calculate_match(candidate, job)
    # Skill: 1/2 * 60 = 30
    assert result["skill_score"] == 30.0
    # Experience: 30 * (2 / 4) = 15
    assert result["experience_score"] == 15.0
    # Culture: 0/1 * 10 = 0
    assert result["culture_score"] == 0.0
    assert result["final_score"] == 45.0
    assert "experience is below the 4-year minimum" in result["reason"]


def test_zero_overlap():
    candidate = {
        "id": 3,
        "name": "No Match",
        "skills": ["gardening"],
        "experience": 0,
        "availability": "Not looking",
        "traits": ["quiet"],
        "quirk": "Prefers plants.",
    }
    job = {
        "id": 3,
        "title": "Cloud Architect",
        "required_skills": ["kubernetes", "terraform"],
        "min_experience": 5,
        "culture_keywords": ["vocal", "fast-paced"],
        "tagline": "Cloud scale.",
    }

    result = calculate_match(candidate, job)
    assert result["skill_score"] == 0.0
    assert result["experience_score"] == 0.0
    assert result["culture_score"] == 0.0
    assert result["final_score"] == 0.0


def test_case_and_whitespace_normalization():
    candidate = {
        "id": 4,
        "name": "Case Insensitive Candidate",
        "skills": ["  Python  ", "SQL"],
        "experience": 5,
        "availability": "Immediate",
        "traits": [" ANALYTICAL "],
        "quirk": "",
    }
    job = {
        "id": 4,
        "title": "Developer",
        "required_skills": ["python", "sql"],
        "min_experience": 3,
        "culture_keywords": ["analytical"],
        "tagline": "",
    }

    result = calculate_match(candidate, job)
    assert result["skill_score"] == 60.0
    assert result["culture_score"] == 10.0
    assert result["experience_score"] == 30.0
    assert result["final_score"] == 100.0


def test_tie_breaking_order():
    job = {
        "id": 1,
        "title": "Tech Lead",
        "required_skills": ["python", "go"],
        "min_experience": 2,
        "culture_keywords": ["collaborative"],
        "tagline": "Lead team.",
    }

    # Cand A: 1 skill (30), meets exp (30), no culture -> 60 total
    cand_a = {
        "id": 10,
        "name": "Bob B.",
        "skills": ["python"],
        "experience": 2,
        "availability": "Immediate",
        "traits": [],
        "quirk": "",
    }
    # Cand B: 0 skill (0), meets exp (30), culture match (10) -> wait, let's create identical scores
    # Cand C: same score, different skill overlap:
    # Say min_exp = 4.
    # Cand C has 1 skill (30) + 2 yrs exp (15) + culture (10) = 55.
    # Let's test two candidates with EXACT same score:
    cand_same_1 = {
        "id": 20,
        "name": "Zach Z.",
        "skills": ["python"],
        "experience": 5,
        "availability": "Immediate",
        "traits": [],
        "quirk": "",
    }
    cand_same_2 = {
        "id": 21,
        "name": "Alice A.",
        "skills": ["python"],
        "experience": 5,
        "availability": "Immediate",
        "traits": [],
        "quirk": "",
    }

    ranked = rank_candidates_for_job(job, [cand_same_1, cand_same_2])
    # Both have score 60 and 1 skill overlap. Alice should come first alphabetically.
    assert ranked[0]["candidate_name"] == "Alice A."
    assert ranked[1]["candidate_name"] == "Zach Z."
