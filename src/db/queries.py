"""CRUD operations for the crypto jobs database."""

import sqlite3
from typing import Optional

from .connection import get_db
from .models import (
    Application,
    Company,
    DiscoveredJob,
    Interview,
    Job,
    JobSkill,
    Skill,
)


# ============== Companies ==============


def create_company(company: Company) -> int:
    """Insert a new company and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO companies (name, website, sector, chain_focus, size, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            company.name,
            company.website,
            company.sector,
            company.chain_focus,
            company.size,
            company.notes,
        ),
    )
    conn.commit()
    company_id = cursor.lastrowid
    conn.close()
    return company_id


def get_company(company_id: int) -> Optional[Company]:
    """Get a company by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    conn.close()
    if row:
        return Company(**dict(row))
    return None


def get_company_by_name(name: str) -> Optional[Company]:
    """Get a company by name (case-insensitive)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM companies WHERE LOWER(name) = LOWER(?)", (name,)
    ).fetchone()
    conn.close()
    if row:
        return Company(**dict(row))
    return None


def list_companies() -> list[Company]:
    """List all companies."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM companies ORDER BY name").fetchall()
    conn.close()
    return [Company(**dict(row)) for row in rows]


def update_company(company: Company) -> None:
    """Update an existing company."""
    conn = get_db()
    conn.execute(
        """
        UPDATE companies
        SET name = ?, website = ?, sector = ?, chain_focus = ?, size = ?, notes = ?
        WHERE id = ?
        """,
        (
            company.name,
            company.website,
            company.sector,
            company.chain_focus,
            company.size,
            company.notes,
            company.id,
        ),
    )
    conn.commit()
    conn.close()


# ============== Jobs ==============


def create_job(job: Job) -> int:
    """Insert a new job and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO jobs (company_id, title, url, salary_min, salary_max,
                         remote_status, date_posted, closing_date, status, source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.company_id,
            job.title,
            job.url,
            job.salary_min,
            job.salary_max,
            job.remote_status,
            job.date_posted,
            job.closing_date,
            job.status,
            job.source,
            job.notes,
        ),
    )
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id


def get_job(job_id: int) -> Optional[Job]:
    """Get a job by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row:
        return Job(**dict(row))
    return None


def list_jobs(status: Optional[str] = None) -> list[Job]:
    """List jobs, optionally filtered by status."""
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY date_found DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY date_found DESC"
        ).fetchall()
    conn.close()
    return [Job(**dict(row)) for row in rows]


def list_jobs_with_sql_skills() -> list[tuple[Job, Company]]:
    """List jobs that require SQL skills."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT DISTINCT j.*, c.*
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        JOIN job_skills js ON j.id = js.job_id
        JOIN skills s ON js.skill_id = s.id
        WHERE s.category = 'SQL'
        ORDER BY j.date_found DESC
        """
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        job = Job(
            id=d["id"],
            company_id=d["company_id"],
            title=d["title"],
            url=d["url"],
            salary_min=d["salary_min"],
            salary_max=d["salary_max"],
            remote_status=d["remote_status"],
            date_posted=d["date_posted"],
            date_found=d["date_found"],
            closing_date=d["closing_date"],
            status=d["status"],
            source=d["source"],
            notes=d["notes"],
        )
        # Company columns have the same names, SQLite returns first match
        # We need a different approach for joins
        result.append(job)
    return result


def update_job(job: Job) -> None:
    """Update an existing job."""
    conn = get_db()
    conn.execute(
        """
        UPDATE jobs
        SET company_id = ?, title = ?, url = ?, salary_min = ?, salary_max = ?,
            remote_status = ?, date_posted = ?, closing_date = ?, status = ?,
            source = ?, notes = ?
        WHERE id = ?
        """,
        (
            job.company_id,
            job.title,
            job.url,
            job.salary_min,
            job.salary_max,
            job.remote_status,
            job.date_posted,
            job.closing_date,
            job.status,
            job.source,
            job.notes,
            job.id,
        ),
    )
    conn.commit()
    conn.close()


# ============== Skills ==============


def get_skill(skill_id: int) -> Optional[Skill]:
    """Get a skill by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    conn.close()
    if row:
        return Skill(**dict(row))
    return None


def get_skill_by_name(name: str) -> Optional[Skill]:
    """Get a skill by name (case-insensitive)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM skills WHERE LOWER(name) = LOWER(?)", (name,)
    ).fetchone()
    conn.close()
    if row:
        return Skill(**dict(row))
    return None


def list_skills(category: Optional[str] = None) -> list[Skill]:
    """List skills, optionally filtered by category."""
    conn = get_db()
    if category:
        rows = conn.execute(
            "SELECT * FROM skills WHERE category = ? ORDER BY name", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM skills ORDER BY name").fetchall()
    conn.close()
    return [Skill(**dict(row)) for row in rows]


def create_skill(skill: Skill) -> int:
    """Insert a new skill and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO skills (name, category) VALUES (?, ?)",
        (skill.name, skill.category),
    )
    conn.commit()
    skill_id = cursor.lastrowid
    conn.close()
    return skill_id


# ============== Job Skills ==============


def add_skill_to_job(job_id: int, skill_id: int, importance: str = "required") -> None:
    """Add a skill to a job."""
    conn = get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO job_skills (job_id, skill_id, importance)
        VALUES (?, ?, ?)
        """,
        (job_id, skill_id, importance),
    )
    conn.commit()
    conn.close()


def remove_skill_from_job(job_id: int, skill_id: int) -> None:
    """Remove a skill from a job."""
    conn = get_db()
    conn.execute(
        "DELETE FROM job_skills WHERE job_id = ? AND skill_id = ?",
        (job_id, skill_id),
    )
    conn.commit()
    conn.close()


def get_job_skills(job_id: int) -> list[tuple[Skill, str]]:
    """Get all skills for a job with their importance."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT s.*, js.importance
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        WHERE js.job_id = ?
        ORDER BY js.importance, s.name
        """,
        (job_id,),
    ).fetchall()
    conn.close()
    return [(Skill(id=r["id"], name=r["name"], category=r["category"]), r["importance"]) for r in rows]


# ============== Applications ==============


def create_application(application: Application) -> int:
    """Insert a new application and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO applications (job_id, date_applied, resume_version,
                                  cover_letter_sent, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            application.job_id,
            application.date_applied,
            application.resume_version,
            1 if application.cover_letter_sent else 0,
            application.status,
            application.notes,
        ),
    )
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return app_id


def get_application(app_id: int) -> Optional[Application]:
    """Get an application by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["cover_letter_sent"] = bool(d["cover_letter_sent"])
        return Application(**d)
    return None


def list_applications(status: Optional[str] = None) -> list[Application]:
    """List applications, optionally filtered by status."""
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY date_applied DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY date_applied DESC"
        ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["cover_letter_sent"] = bool(d["cover_letter_sent"])
        result.append(Application(**d))
    return result


def update_application(application: Application) -> None:
    """Update an existing application."""
    conn = get_db()
    conn.execute(
        """
        UPDATE applications
        SET job_id = ?, date_applied = ?, resume_version = ?,
            cover_letter_sent = ?, status = ?, notes = ?
        WHERE id = ?
        """,
        (
            application.job_id,
            application.date_applied,
            application.resume_version,
            1 if application.cover_letter_sent else 0,
            application.status,
            application.notes,
            application.id,
        ),
    )
    conn.commit()
    conn.close()


# ============== Interviews ==============


def create_interview(interview: Interview) -> int:
    """Insert a new interview and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO interviews (application_id, scheduled_at, type, notes, outcome)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            interview.application_id,
            interview.scheduled_at,
            interview.type,
            interview.notes,
            interview.outcome,
        ),
    )
    conn.commit()
    interview_id = cursor.lastrowid
    conn.close()
    return interview_id


def get_interview(interview_id: int) -> Optional[Interview]:
    """Get an interview by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM interviews WHERE id = ?", (interview_id,)
    ).fetchone()
    conn.close()
    if row:
        return Interview(**dict(row))
    return None


def list_interviews(application_id: Optional[int] = None) -> list[Interview]:
    """List interviews, optionally filtered by application."""
    conn = get_db()
    if application_id:
        rows = conn.execute(
            "SELECT * FROM interviews WHERE application_id = ? ORDER BY scheduled_at",
            (application_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM interviews ORDER BY scheduled_at DESC"
        ).fetchall()
    conn.close()
    return [Interview(**dict(row)) for row in rows]


def update_interview(interview: Interview) -> None:
    """Update an existing interview."""
    conn = get_db()
    conn.execute(
        """
        UPDATE interviews
        SET application_id = ?, scheduled_at = ?, type = ?, notes = ?, outcome = ?
        WHERE id = ?
        """,
        (
            interview.application_id,
            interview.scheduled_at,
            interview.type,
            interview.notes,
            interview.outcome,
            interview.id,
        ),
    )
    conn.commit()
    conn.close()


# ============== Discovered Jobs ==============


def create_discovered_job(job: DiscoveredJob) -> int:
    """Insert a new discovered job and return its ID."""
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO discovered_jobs (title, company_name, url, requirements_raw,
                                     source, raw_response, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.title,
            job.company_name,
            job.url,
            job.requirements_raw,
            job.source,
            job.raw_response,
            job.status,
        ),
    )
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id


def get_discovered_job(job_id: int) -> Optional[DiscoveredJob]:
    """Get a discovered job by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM discovered_jobs WHERE id = ?", (job_id,)
    ).fetchone()
    conn.close()
    if row:
        return DiscoveredJob(**dict(row))
    return None


def list_discovered_jobs(status: Optional[str] = None) -> list[DiscoveredJob]:
    """List discovered jobs, optionally filtered by status."""
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM discovered_jobs WHERE status = ? ORDER BY discovered_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM discovered_jobs ORDER BY discovered_at DESC"
        ).fetchall()
    conn.close()
    return [DiscoveredJob(**dict(row)) for row in rows]


def update_discovered_job_status(job_id: int, status: str, promoted_to_job_id: Optional[int] = None) -> None:
    """Update a discovered job's status."""
    conn = get_db()
    conn.execute(
        """
        UPDATE discovered_jobs
        SET status = ?, promoted_to_job_id = ?
        WHERE id = ?
        """,
        (status, promoted_to_job_id, job_id),
    )
    conn.commit()
    conn.close()


def discovered_job_exists(url: str) -> bool:
    """Check if a discovered job with this URL already exists."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM discovered_jobs WHERE url = ?", (url,)
    ).fetchone()
    conn.close()
    return row is not None


def job_url_exists(url: str) -> bool:
    """Check if a job with this URL already exists."""
    conn = get_db()
    row = conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None
