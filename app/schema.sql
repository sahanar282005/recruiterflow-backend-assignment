-- Schema for RecruiterFlow Bot
-- SQLite handwritten DDL

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    skills TEXT NOT NULL,          -- JSON array of strings, e.g. ["deduction", "pattern-recognition", "forensics"]
    experience INTEGER NOT NULL CHECK (experience >= 0),
    availability TEXT NOT NULL,
    traits TEXT NOT NULL,          -- JSON array of strings, e.g. ["analytical", "blunt"]
    quirk TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    required_skills TEXT NOT NULL, -- JSON array of strings, e.g. ["deduction", "pattern-recognition", "forensics"]
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    culture_keywords TEXT NOT NULL, -- JSON array of strings, e.g. ["analytical", "autonomous"]
    tagline TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
