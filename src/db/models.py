"""Data models for the crypto jobs database."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Company:
    id: Optional[int] = None
    name: str = ""
    website: Optional[str] = None
    sector: Optional[str] = None  # DeFi, NFT, Infrastructure, Exchange, Analytics, Other
    chain_focus: Optional[str] = None
    size: Optional[str] = None  # startup, small, medium, large
    notes: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Job:
    id: Optional[int] = None
    company_id: int = 0
    title: str = ""
    url: Optional[str] = None
    salary_min: Optional[int] = None  # USD annual
    salary_max: Optional[int] = None  # USD annual
    remote_status: Optional[str] = None  # remote, hybrid, onsite
    date_posted: Optional[str] = None
    date_found: Optional[str] = None
    closing_date: Optional[str] = None
    status: str = "open"  # open, closed, expired
    source: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Skill:
    id: Optional[int] = None
    name: str = ""
    category: Optional[str] = None  # SQL, Programming, Cloud, BI, Blockchain


@dataclass
class JobSkill:
    job_id: int = 0
    skill_id: int = 0
    importance: str = "required"  # required, nice-to-have


@dataclass
class Application:
    id: Optional[int] = None
    job_id: int = 0
    date_applied: Optional[str] = None
    resume_version: Optional[str] = None
    cover_letter_sent: bool = False
    status: str = "applied"  # applied, screening, interview, rejected, offer, ghosted, withdrawn
    notes: Optional[str] = None


@dataclass
class Interview:
    id: Optional[int] = None
    application_id: int = 0
    scheduled_at: Optional[str] = None  # ISO 8601 datetime
    type: Optional[str] = None  # recruiter, technical, sql-challenge, culture, final
    notes: Optional[str] = None
    outcome: Optional[str] = None  # passed, failed, pending, cancelled


@dataclass
class DiscoveredJob:
    id: Optional[int] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    url: Optional[str] = None
    requirements_raw: Optional[str] = None
    source: Optional[str] = None
    raw_response: Optional[str] = None
    discovered_at: Optional[str] = None
    status: str = "pending"  # pending, saved, dismissed, promoted
    promoted_to_job_id: Optional[int] = None
