"""
Ingestion module for live job posting APIs (Techmap & JSearch).

Note:
  - This module requires valid API credentials configured in a `.env` file or environment variables.
  - If no credentials are configured, the web application runs in Demo or Upload mode.
  - Free tiers:
      * Techmap: 1,000 jobs/month (skills pre-tagged).
      * JSearch (RapidAPI): 200 requests/month (aggregates Google for Jobs/Indeed/Glassdoor).

Usage:
    python ingest.py --source techmap --query "data analyst" --pages 2
    python ingest.py --source jsearch --query "software engineer" --pages 2
"""

import os
import json
import time
import argparse
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests

RAW_DIR = "raw_postings"
os.makedirs(RAW_DIR, exist_ok=True)


def check_api_credentials(source: str) -> Optional[str]:
    """Check if the API key for the requested source is available in environment."""
    if source == "techmap":
        key = os.getenv("TECHMAP_API_KEY")
        if not key or key.strip() in ("", "YOUR_TECHMAP_API_KEY"):
            return None
        return key.strip()
    elif source == "jsearch":
        key = os.getenv("RAPIDAPI_KEY")
        if not key or key.strip() in ("", "YOUR_RAPIDAPI_KEY"):
            return None
        return key.strip()
    return None


def fetch_techmap(query: str, pages: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch job postings from Techmap Jobs API.
    Techmap returns a `skills` array already extracted per posting.
    """
    api_key = check_api_credentials("techmap")
    if not api_key:
        raise ValueError(
            "Missing TECHMAP_API_KEY. Set TECHMAP_API_KEY in your .env file or environment."
        )

    results = []
    print(f"[Techmap] Fetching {pages} page(s) for query: '{query}'...")
    for page in range(1, pages + 1):
        resp = requests.get(
            "https://api.techmap.io/jobs-api",
            params={"q": query, "page": page},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        page_results = data.get("result", [])
        results.extend(page_results)
        print(f"  Page {page}: retrieved {len(page_results)} postings.")
        if page < pages:
            time.sleep(1)  # Respect free tier rate limits
    return results


def fetch_jsearch(query: str, pages: int = 2) -> List[Dict[str, Any]]:
    """
    Fetch job postings from JSearch API via RapidAPI.
    Skills must be extracted from the free-text `job_description` field.
    """
    api_key = check_api_credentials("jsearch")
    if not api_key:
        raise ValueError(
            "Missing RAPIDAPI_KEY. Set RAPIDAPI_KEY in your .env file or environment."
        )

    results = []
    print(f"[JSearch] Fetching {pages} page(s) for query: '{query}'...")
    for page in range(1, pages + 1):
        resp = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            params={"query": query, "page": page, "num_pages": 1},
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        page_results = data.get("data", [])
        results.extend(page_results)
        print(f"  Page {page}: retrieved {len(page_results)} postings.")
        if page < pages:
            time.sleep(1)
    return results


def normalize_api_data(raw_postings: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    """Map each API source's response schema onto the common standardized dictionary shape."""
    normalized = []
    for p in raw_postings:
        if source == "techmap":
            normalized.append({
                "source": "techmap",
                "title": p.get("title") or "Untitled Position",
                "company": p.get("company") or "Unknown Company",
                "country": p.get("countryCode") or "N/A",
                "posted_at": p.get("dateCreated") or "N/A",
                "skills_raw": p.get("skills", []),  # Pre-tagged
                "description": p.get("description") or "",
            })
        elif source == "jsearch":
            normalized.append({
                "source": "jsearch",
                "title": p.get("job_title") or "Untitled Position",
                "company": p.get("employer_name") or "Unknown Company",
                "country": p.get("job_country") or "N/A",
                "posted_at": p.get("job_posted_at_datetime_utc") or "N/A",
                "skills_raw": None,  # Requires extraction
                "description": p.get("job_description") or "",
            })
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch job postings from live APIs.")
    parser.add_argument("--source", choices=["techmap", "jsearch"], required=True, help="API source")
    parser.add_argument("--query", required=True, help="Job title or search keyword")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages to retrieve")
    args = parser.parse_args()

    try:
        fetch_fn = fetch_techmap if args.source == "techmap" else fetch_jsearch
        raw = fetch_fn(args.query, args.pages)
        norm = normalize_api_data(raw, args.source)

        safe_query = args.query.replace(" ", "_").replace("/", "_")
        out_path = os.path.join(RAW_DIR, f"{args.source}_{safe_query}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(norm, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(norm)} normalized postings to {out_path}")
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
