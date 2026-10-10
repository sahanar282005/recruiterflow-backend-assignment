-- Schema for RecruiterFlow Bot
-- SQLite handwritten DDL with normalized relational tables

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

CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_candidate_skills_cand_id ON candidate_skills(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_traits_cand_id ON candidate_traits(candidate_id);
CREATE INDEX IF NOT EXISTS idx_job_required_skills_job_id ON job_required_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_culture_keywords_job_id ON job_culture_keywords(job_id);
