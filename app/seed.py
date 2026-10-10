"""Deterministic ingestion script for candidates and jobs with normalized relational tables."""

from typing import Optional
from app.database import get_db_connection, init_db

CANDIDATES_DATA = [
    {
        "name": "Sherlock H.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "experience": 8,
        "availability": "Immediate",
        "traits": ["analytical", "blunt"],
        "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
    },
    {
        "name": "Hermione G.",
        "skills": ["research", "time-management", "public-speaking"],
        "experience": 4,
        "availability": "2 weeks",
        "traits": ["detail-oriented", "overachiever"],
        "quirk": "Reads the entire documentation before writing a single line of code.",
    },
    {
        "name": "Tony S.",
        "skills": ["systems-design", "rapid-prototyping", "leadership"],
        "experience": 12,
        "availability": "Not looking",
        "traits": ["confident", "innovative"],
        "quirk": "Ships an MVP overnight, refuses to write tests.",
    },
    {
        "name": "Leslie K.",
        "skills": ["project-management", "stakeholder-management", "public-speaking"],
        "experience": 6,
        "availability": "Immediate",
        "traits": ["tenacious", "organized"],
        "quirk": "Has a binder for everything, including the binder.",
    },
    {
        "name": "Ron S.",
        "skills": ["woodworking", "minimalism", "negotiation"],
        "experience": 15,
        "availability": "Not looking",
        "traits": ["stubborn", "principled"],
        "quirk": "Refuses to use more than one monitor.",
    },
    {
        "name": "Rick S.",
        "skills": ["systems-design", "rapid-prototyping", "chemistry"],
        "experience": 20,
        "availability": "Immediate",
        "traits": ["genius", "reckless"],
        "quirk": "Solution works, mechanism deeply concerning.",
    },
    {
        "name": "Elle W.",
        "skills": ["persuasion", "research", "public-speaking"],
        "experience": 3,
        "availability": "Immediate",
        "traits": ["optimistic", "sharp"],
        "quirk": "Underestimated in every standup, correct in every retro.",
    },
    {
        "name": "MacGyver",
        "skills": ["rapid-prototyping", "resourcefulness", "chemistry", "systems-design"],
        "experience": 10,
        "availability": "2 weeks",
        "traits": ["calm", "improviser"],
        "quirk": "Fixes production outages with duct tape and a paperclip metaphor.",
    },
    {
        "name": "Sheldon C.",
        "skills": ["theoretical-analysis", "pattern-recognition", "research"],
        "experience": 9,
        "availability": "Immediate",
        "traits": ["rigid", "brilliant"],
        "quirk": "Correct 95% of the time, insufferable 100% of the time.",
    },
    {
        "name": "Katniss E.",
        "skills": ["precision", "strategy", "crisis-management"],
        "experience": 5,
        "availability": "Immediate",
        "traits": ["resilient", "decisive"],
        "quirk": "Excellent under pressure, terrible with public speaking.",
    },
    {
        "name": "Michael S.",
        "skills": ["sales", "public-speaking", "team-building"],
        "experience": 11,
        "availability": "Not looking",
        "traits": ["enthusiastic", "chaotic"],
        "quirk": "World's best boss, according to a mug he bought himself.",
    },
    {
        "name": "Olivia P.",
        "skills": ["crisis-management", "negotiation", "strategy", "leadership"],
        "experience": 13,
        "availability": "2 weeks",
        "traits": ["decisive", "intense"],
        "quirk": "Handles it. Whatever it is.",
    },
    {
        "name": "Ted L.",
        "skills": ["team-building", "optimism", "mentorship", "public-speaking"],
        "experience": 7,
        "availability": "Immediate",
        "traits": ["empathetic", "persistent"],
        "quirk": "Turns every technical setback into a folksy metaphor.",
    },
    {
        "name": "Miranda P.",
        "skills": ["leadership", "negotiation", "stakeholder-management", "precision"],
        "experience": 18,
        "availability": "Not looking",
        "traits": ["demanding", "decisive"],
        "quirk": "Reviews every PR personally. Says nothing. Everyone panics.",
    },
    {
        "name": "Dwight S.",
        "skills": ["sales", "negotiation", "security", "loyalty"],
        "experience": 9,
        "availability": "Immediate",
        "traits": ["intense", "loyal"],
        "quirk": "Assistant to the regional backend engineer.",
    },
]

JOBS_DATA = [
    {
        "title": "Backend Detective",
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "min_experience": 3,
        "culture_keywords": ["analytical", "autonomous"],
        "tagline": "We have a bug. We have no leads. We have you.",
    },
    {
        "title": "Rapid Prototyping Engineer",
        "required_skills": ["rapid-prototyping", "systems-design"],
        "min_experience": 2,
        "culture_keywords": ["innovative", "fast-paced"],
        "tagline": "Ship first, document never (kidding — please document).",
    },
    {
        "title": "Developer Relations Lead",
        "required_skills": ["public-speaking", "research"],
        "min_experience": 2,
        "culture_keywords": ["energetic", "curious"],
        "tagline": "Explain complex things to confused humans, cheerfully.",
    },
    {
        "title": "Engineering Manager, Chaos Team",
        "required_skills": ["team-building", "stakeholder-management", "leadership"],
        "min_experience": 5,
        "culture_keywords": ["empathetic", "organized"],
        "tagline": "Herd cats. The cats are senior engineers.",
    },
    {
        "title": "Incident Commander",
        "required_skills": ["crisis-management", "strategy", "negotiation"],
        "min_experience": 4,
        "culture_keywords": ["decisive", "calm-under-pressure"],
        "tagline": "3am page. You're the one who picks up.",
    },
    {
        "title": "Sales Engineer",
        "required_skills": ["sales", "public-speaking", "negotiation"],
        "min_experience": 3,
        "culture_keywords": ["enthusiastic", "persistent"],
        "tagline": "Sell the vision, then go build it.",
    },
]


def seed_database(db_path: Optional[str] = None) -> tuple[int, int]:
    """Seed the database deterministically without duplicates using normalized relational tables.
    
    Returns (candidate_count, job_count).
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Upsert candidates
            for c in CANDIDATES_DATA:
                conn.execute(
                    """
                    INSERT INTO candidates (name, experience, availability, quirk)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        experience = excluded.experience,
                        availability = excluded.availability,
                        quirk = excluded.quirk;
                    """,
                    (c["name"], c["experience"], c["availability"], c["quirk"]),
                )
                cand_id = conn.execute(
                    "SELECT id FROM candidates WHERE name = ?;", (c["name"],)
                ).fetchone()[0]

                # Populate candidate_skills
                conn.execute(
                    "DELETE FROM candidate_skills WHERE candidate_id = ?;", (cand_id,)
                )
                conn.executemany(
                    "INSERT INTO candidate_skills (candidate_id, skill) VALUES (?, ?);",
                    [(cand_id, s) for s in c["skills"]],
                )

                # Populate candidate_traits
                conn.execute(
                    "DELETE FROM candidate_traits WHERE candidate_id = ?;", (cand_id,)
                )
                conn.executemany(
                    "INSERT INTO candidate_traits (candidate_id, trait) VALUES (?, ?);",
                    [(cand_id, t) for t in c["traits"]],
                )

            # 2. Upsert jobs
            for j in JOBS_DATA:
                conn.execute(
                    """
                    INSERT INTO jobs (title, min_experience, tagline)
                    VALUES (?, ?, ?)
                    ON CONFLICT(title) DO UPDATE SET
                        min_experience = excluded.min_experience,
                        tagline = excluded.tagline;
                    """,
                    (j["title"], j["min_experience"], j["tagline"]),
                )
                job_id = conn.execute(
                    "SELECT id FROM jobs WHERE title = ?;", (j["title"],)
                ).fetchone()[0]

                # Populate job_required_skills
                conn.execute(
                    "DELETE FROM job_required_skills WHERE job_id = ?;", (job_id,)
                )
                conn.executemany(
                    "INSERT INTO job_required_skills (job_id, skill) VALUES (?, ?);",
                    [(job_id, s) for s in j["required_skills"]],
                )

                # Populate job_culture_keywords
                conn.execute(
                    "DELETE FROM job_culture_keywords WHERE job_id = ?;", (job_id,)
                )
                conn.executemany(
                    "INSERT INTO job_culture_keywords (job_id, keyword) VALUES (?, ?);",
                    [(job_id, k) for k in j["culture_keywords"]],
                )

        candidate_count = conn.execute("SELECT COUNT(*) FROM candidates;").fetchone()[0]
        job_count = conn.execute("SELECT COUNT(*) FROM jobs;").fetchone()[0]
        return candidate_count, job_count
    finally:
        conn.close()


if __name__ == "__main__":
    c_count, j_count = seed_database()
    print(f"Database seeded successfully: {c_count} candidates, {j_count} jobs.")
