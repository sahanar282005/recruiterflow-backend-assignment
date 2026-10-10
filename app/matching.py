"""Deterministic matching algorithm for candidates and jobs."""

from typing import Any


def normalize_token(token: str) -> str:
    """Normalize token by stripping whitespace and converting to lowercase."""
    return token.strip().lower()


def normalize_tokens(tokens: list[str]) -> set[str]:
    """Normalize a list of tokens into a set of unique normalized strings."""
    return {normalize_token(t) for t in tokens if t and t.strip()}


def calculate_match(candidate: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """Calculate matching score and reason between a candidate and a job.
    
    Weights:
      - Skill overlap: 60 points
      - Experience fit: 30 points
      - Culture/trait alignment: 10 points
      - Total possible: 100 points
    
    Returns a dict with:
      - final_score: float rounded to 2 decimal places
      - skill_score: float
      - experience_score: float
      - culture_score: float
      - skill_overlap_count: int
      - total_required_skills: int
      - culture_overlap_count: int
      - total_culture_keywords: int
      - reason: str
    """
    candidate_skills = normalize_tokens(candidate.get("skills", []))
    required_skills = normalize_tokens(job.get("required_skills", []))
    total_required_skills = len(required_skills)
    skill_overlap = candidate_skills.intersection(required_skills)
    skill_overlap_count = len(skill_overlap)

    if total_required_skills > 0:
        skill_score = (skill_overlap_count / total_required_skills) * 60.0
    else:
        skill_score = 0.0

    cand_exp = candidate.get("experience", 0)
    min_exp = job.get("min_experience", 0)

    if min_exp <= 0:
        experience_score = 30.0
        exp_reason = "experience meets the minimum"
    elif cand_exp >= min_exp:
        experience_score = 30.0
        exp_reason = f"experience meets the {min_exp}-year minimum"
    else:
        experience_score = 30.0 * (cand_exp / min_exp)
        exp_reason = f"experience is below the {min_exp}-year minimum"

    candidate_traits = normalize_tokens(candidate.get("traits", []))
    culture_keywords = normalize_tokens(job.get("culture_keywords", []))
    total_culture_keywords = len(culture_keywords)
    culture_overlap = candidate_traits.intersection(culture_keywords)
    culture_overlap_count = len(culture_overlap)

    if total_culture_keywords > 0:
        culture_score = (culture_overlap_count / total_culture_keywords) * 10.0
    else:
        culture_score = 0.0

    raw_total = skill_score + experience_score + culture_score
    final_score = round(raw_total, 2)

    reason = (
        f"Matches {skill_overlap_count} of {total_required_skills} required skills; "
        f"{exp_reason}; "
        f"culture alignment {culture_overlap_count} of {total_culture_keywords}."
    )

    return {
        "final_score": final_score,
        "skill_score": round(skill_score, 2),
        "experience_score": round(experience_score, 2),
        "culture_score": round(culture_score, 2),
        "skill_overlap_count": skill_overlap_count,
        "total_required_skills": total_required_skills,
        "culture_overlap_count": culture_overlap_count,
        "total_culture_keywords": total_culture_keywords,
        "reason": reason,
    }


def rank_candidates_for_job(job: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidates for a specific job in descending order with deterministic tie-breaking.
    
    Tie-breaking order:
      1. Score (descending)
      2. Skill overlap count (descending)
      3. Candidate name (alphabetical ascending)
      4. Candidate ID (ascending)
    """
    scored_candidates = []
    for cand in candidates:
        match_result = calculate_match(cand, job)
        scored_candidates.append({
            "candidate_id": cand["id"],
            "candidate_name": cand["name"],
            "score": match_result["final_score"],
            "reason": match_result["reason"],
            "_skill_overlap_count": match_result["skill_overlap_count"],
        })

    scored_candidates.sort(
        key=lambda x: (
            -x["score"],
            -x["_skill_overlap_count"],
            x["candidate_name"].lower(),
            x["candidate_id"],
        )
    )

    # Clean internal sorting fields
    for item in scored_candidates:
        item.pop("_skill_overlap_count", None)

    return scored_candidates


def rank_jobs_for_candidate(candidate: dict[str, Any], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank jobs for a specific candidate in descending order with deterministic tie-breaking.
    
    Tie-breaking order:
      1. Score (descending)
      2. Skill overlap count (descending)
      3. Job title (alphabetical ascending)
      4. Job ID (ascending)
    """
    scored_jobs = []
    for job in jobs:
        match_result = calculate_match(candidate, job)
        scored_jobs.append({
            "job_id": job["id"],
            "job_title": job["title"],
            "score": match_result["final_score"],
            "reason": match_result["reason"],
            "_skill_overlap_count": match_result["skill_overlap_count"],
        })

    scored_jobs.sort(
        key=lambda x: (
            -x["score"],
            -x["_skill_overlap_count"],
            x["job_title"].lower(),
            x["job_id"],
        )
    )

    # Clean internal sorting fields
    for item in scored_jobs:
        item.pop("_skill_overlap_count", None)

    return scored_jobs
