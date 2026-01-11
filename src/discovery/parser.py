"""Parse Perplexity API responses into structured job data."""

import json
import re
from typing import Optional


def extract_json_from_response(raw_response: str) -> Optional[str]:
    """
    Extract JSON array from API response.

    The response might contain markdown code blocks or extra text.
    This function tries to find and extract the JSON array.
    """
    if not raw_response:
        return None

    # Try to find JSON array in the response
    # First, try to parse the whole response as JSON
    try:
        json.loads(raw_response)
        return raw_response
    except json.JSONDecodeError:
        pass

    # Look for JSON array in markdown code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(code_block_pattern, raw_response)
    for match in matches:
        try:
            json.loads(match.strip())
            return match.strip()
        except json.JSONDecodeError:
            continue

    # Look for JSON array pattern [...] in the response
    array_pattern = r"\[[\s\S]*\]"
    matches = re.findall(array_pattern, raw_response)
    for match in matches:
        try:
            json.loads(match)
            return match
        except json.JSONDecodeError:
            continue

    return None


def parse_jobs(raw_response: str) -> list[dict]:
    """
    Parse raw API response into a list of job dictionaries.

    Returns a list of dicts with keys:
    - title: str
    - company: str (company_name)
    - url: str
    - requirements: str (requirements_raw)
    - parse_error: bool (True if this job had parsing issues)
    """
    json_str = extract_json_from_response(raw_response)

    if not json_str:
        # Return a single error entry if we can't parse at all
        return [{
            "title": "[PARSE ERROR]",
            "company": "Unknown",
            "url": None,
            "requirements": raw_response[:500] if raw_response else "Empty response",
            "parse_error": True
        }]

    try:
        jobs_data = json.loads(json_str)

        if not isinstance(jobs_data, list):
            jobs_data = [jobs_data]

        parsed_jobs = []
        for job in jobs_data:
            if not isinstance(job, dict):
                continue

            parsed_job = {
                "title": job.get("title", "[No Title]"),
                "company": job.get("company", "Unknown"),
                "url": job.get("url"),
                "requirements": job.get("requirements", ""),
                "parse_error": False
            }

            # Validate URL
            url = parsed_job.get("url")
            if url and not (url.startswith("http://") or url.startswith("https://")):
                parsed_job["url"] = None
                parsed_job["parse_error"] = True

            parsed_jobs.append(parsed_job)

        return parsed_jobs if parsed_jobs else [{
            "title": "[PARSE ERROR]",
            "company": "Unknown",
            "url": None,
            "requirements": "No valid jobs found in response",
            "parse_error": True
        }]

    except json.JSONDecodeError as e:
        return [{
            "title": "[PARSE ERROR]",
            "company": "Unknown",
            "url": None,
            "requirements": f"JSON decode error: {str(e)}",
            "parse_error": True
        }]


def validate_job(job: dict) -> tuple[bool, str]:
    """
    Validate a parsed job has required fields.

    Returns:
        (is_valid, reason)
    """
    if not job.get("title") or job["title"] == "[PARSE ERROR]":
        return False, "Missing or invalid title"

    if not job.get("url"):
        return False, "Missing URL"

    if job.get("parse_error"):
        return False, "Parse error flag set"

    return True, "Valid"
