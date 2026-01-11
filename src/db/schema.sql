-- Crypto Jobs Database Schema
-- Run this to create all tables

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    website TEXT,
    sector TEXT,  -- DeFi, NFT, Infrastructure, Exchange, Analytics, Other
    chain_focus TEXT,  -- Free text: "Ethereum", "Solana, Polygon", etc.
    size TEXT,  -- startup, small, medium, large
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    salary_min INTEGER,  -- USD annual
    salary_max INTEGER,  -- USD annual
    remote_status TEXT,  -- remote, hybrid, onsite
    date_posted TEXT,
    date_found TEXT DEFAULT CURRENT_DATE,
    closing_date TEXT,
    status TEXT DEFAULT 'open',  -- open, closed, expired
    source TEXT,
    notes TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT  -- SQL, Programming, Cloud, BI, Blockchain
);

-- Job-Skills junction table (many-to-many)
CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    importance TEXT DEFAULT 'required',  -- required, nice-to-have
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    date_applied TEXT DEFAULT CURRENT_DATE,
    resume_version TEXT,
    cover_letter_sent INTEGER DEFAULT 0,  -- Boolean: 0 or 1
    status TEXT DEFAULT 'applied',  -- applied, screening, interview, rejected, offer, ghosted, withdrawn
    notes TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    scheduled_at TEXT,  -- ISO 8601 datetime
    type TEXT,  -- recruiter, technical, sql-challenge, culture, final
    notes TEXT,
    outcome TEXT,  -- passed, failed, pending, cancelled
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- Discovered jobs staging table (Phase 2)
CREATE TABLE IF NOT EXISTS discovered_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    company_name TEXT,
    url TEXT UNIQUE,
    requirements_raw TEXT,
    source TEXT,  -- "perplexity"
    raw_response TEXT,  -- Full API response for debugging
    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',  -- pending, saved, dismissed, promoted
    promoted_to_job_id INTEGER,
    FOREIGN KEY (promoted_to_job_id) REFERENCES jobs(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_skills_job ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_interviews_application ON interviews(application_id);
CREATE INDEX IF NOT EXISTS idx_discovered_jobs_status ON discovered_jobs(status);
