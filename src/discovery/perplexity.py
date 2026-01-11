"""Perplexity API client for job discovery."""

import os
import json
import requests
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

SYSTEM_PROMPT = """You are a job search assistant. Find crypto/web3 job postings and return them as a JSON array.

For each job found, include these fields:
- title: job title
- company: company name
- url: direct link to the job posting (must be a valid URL)
- requirements: key requirements/skills mentioned (as a string)

IMPORTANT: Return ONLY a valid JSON array, no explanation or markdown. Example format:
[{"title": "Data Analyst", "company": "Uniswap", "url": "https://...", "requirements": "SQL, Python, 3+ years"}]

If you cannot find any jobs, return an empty array: []"""

DEFAULT_USER_PROMPT = """Find remote crypto/web3 jobs posted in the last 7 days that require SQL or data analytics skills. Return up to 10 results."""


def get_api_key() -> Optional[str]:
    """Get Perplexity API key from environment."""
    return os.environ.get("PERPLEXITY_API_KEY")


def search_jobs(user_prompt: str = DEFAULT_USER_PROMPT) -> dict:
    """
    Search for jobs using Perplexity API.

    Returns:
        dict with keys:
        - success: bool
        - raw_response: str (full API response for debugging)
        - jobs: list of parsed job dicts (if successful)
        - error: str (if failed)
    """
    api_key = get_api_key()

    if not api_key:
        return {
            "success": False,
            "raw_response": "",
            "jobs": [],
            "error": "PERPLEXITY_API_KEY environment variable not set"
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Low temperature for consistent JSON output
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()
        raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        return {
            "success": True,
            "raw_response": raw_content,
            "jobs": [],  # Will be parsed by parser.py
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "raw_response": "",
            "jobs": [],
            "error": "API request timed out"
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "raw_response": str(e.response.text) if e.response else "",
            "jobs": [],
            "error": f"HTTP error: {e.response.status_code if e.response else 'unknown'}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "raw_response": "",
            "jobs": [],
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "raw_response": "",
            "jobs": [],
            "error": f"Unexpected error: {str(e)}"
        }
