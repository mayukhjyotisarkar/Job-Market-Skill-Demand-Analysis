"""
Extraction and analytical processing module for job posting skill demand.

Handles regex compilation with safe boundary matching, skill extraction,
posting deduplication, frequency ranking, co-occurrence analysis, and
drill-down inspection helpers.
"""

import re
import json
import itertools
from collections import Counter
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from taxonomy import DEFAULT_SKILL_SYNONYMS, get_category_for_skill


def build_regex_pattern(term: str) -> str:
    """
    Build a regex pattern with appropriate word/boundary assertions.
    Handles tricky terms ending in non-word symbols like 'c++' or 'c#'
    as well as single-letter tokens like 'r' or 'c'.
    """
    term = term.strip()
    # If the pattern already includes explicit regex boundary syntax, preserve it
    if term.startswith(r"\b") or "(?<=" in term or "(?=" in term:
        return term

    escaped = re.escape(term)
    prefix = r"\b" if re.match(r"^\w", term) else r"(?:^|(?<=[\s,;:(\[\{/]))"
    suffix = r"\b" if re.match(r".*\w$", term) else r"(?:$|(?=[\s,;:.)\]\}/]))"
    return f"{prefix}{escaped}{suffix}"


def compile_taxonomy(taxonomy_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    """Compile dictionary of canonical skill -> list of terms into case-insensitive regexes."""
    compiled = {}
    for skill, terms in taxonomy_dict.items():
        if not terms:
            continue
        patterns = [build_regex_pattern(t) for t in terms if t.strip()]
        if patterns:
            compiled[skill] = re.compile("|".join(patterns), re.IGNORECASE)
    return compiled


# Default compiled patterns
_DEFAULT_COMPILED = compile_taxonomy(DEFAULT_SKILL_SYNONYMS)


def extract_skills(text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None) -> List[str]:
    """
    Extract canonical skills from arbitrary free text using the compiled taxonomy.
    Returns a sorted list of unique matched skill names.
    """
    if not text or not isinstance(text, str):
        return []

    compiled = compiled_taxonomy if compiled_taxonomy is not None else _DEFAULT_COMPILED
    found = []
    for skill, pattern in compiled.items():
        if pattern.search(text):
            found.append(skill)
    return sorted(set(found))


def normalize_posting(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize inconsistent field names from various JSON/CSV schemas.
    Accepts keys like job_title, employer_name, text, description, etc.
    """
    title = p.get("title") or p.get("job_title") or p.get("position") or "Untitled Position"
    company = p.get("company") or p.get("employer_name") or p.get("employer") or p.get("company_name") or "Unknown Company"
    posted_at = p.get("posted_at") or p.get("job_posted_at_datetime_utc") or p.get("dateCreated") or p.get("date") or "N/A"
    
    # Description resolution
    description = p.get("description") or p.get("job_description") or p.get("summary") or p.get("text") or ""
    if not isinstance(description, str):
        description = "" if pd.isna(description) else str(description)

    # Pre-tagged skills resolution (could be a list or comma-separated string)
    skills_raw = p.get("skills_raw") or p.get("skills") or p.get("tags") or p.get("job_skills")
    parsed_skills_raw = []
    if isinstance(skills_raw, list):
        parsed_skills_raw = [str(s).strip() for s in skills_raw if str(s).strip()]
    elif isinstance(skills_raw, str) and skills_raw.strip():
        # Handle comma or semicolon separated string of tags
        parsed_skills_raw = [s.strip() for s in re.split(r"[,;|]", skills_raw) if s.strip()]

    return {
        "title": str(title).strip(),
        "company": str(company).strip(),
        "posted_at": str(posted_at).strip(),
        "description": description.strip(),
        "skills_raw": parsed_skills_raw,
    }


def deduplicate_postings(postings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Identify and remove duplicate job postings based on title + company + first 100 chars of description.
    Returns (deduplicated_list, number_of_duplicates_removed).
    """
    seen = set()
    unique_postings = []
    duplicates_count = 0

    for p in postings:
        norm = normalize_posting(p)
        desc_snippet = (norm["description"][:120]).lower().strip()
        key = (norm["title"].lower(), norm["company"].lower(), desc_snippet)
        if key in seen:
            duplicates_count += 1
            continue
        seen.add(key)
        unique_postings.append(p)

    return unique_postings, duplicates_count


def build_skill_frame(
    postings: List[Dict[str, Any]],
    taxonomy_dict: Optional[Dict[str, List[str]]] = None,
    skill_source_mode: str = "auto",  # 'auto', 'extracted_only', 'source_tags_only', 'combined'
) -> pd.DataFrame:
    """
    Convert raw postings into an enriched DataFrame with extracted/source skills.
    
    skill_source_mode:
      - 'auto': Uses source tags if present and non-empty; otherwise extracts from description.
      - 'extracted_only': Forces extraction from description text even if tags exist.
      - 'source_tags_only': Uses only pre-tagged skills from data source.
      - 'combined': Merges both source tags and extracted skills.
    """
    compiled = compile_taxonomy(taxonomy_dict) if taxonomy_dict is not None else _DEFAULT_COMPILED
    rows = []

    for idx, raw_p in enumerate(postings):
        p = normalize_posting(raw_p)
        has_source_tags = bool(p["skills_raw"])
        has_description = bool(p["description"])

        # 1. Extract from description
        extracted = extract_skills(p["description"], compiled_taxonomy=compiled) if has_description else []

        # 2. Normalize source tags against taxonomy if possible
        normalized_source_tags = []
        if has_source_tags:
            for s in p["skills_raw"]:
                # Check if the tag matches any canonical skill
                matched = extract_skills(s, compiled_taxonomy=compiled)
                if matched:
                    normalized_source_tags.extend(matched)
                else:
                    normalized_source_tags.append(s)
            normalized_source_tags = sorted(set(normalized_source_tags))

        # 3. Apply mode
        if skill_source_mode == "source_tags_only":
            final_skills = normalized_source_tags
            origin = "Source Tags" if has_source_tags else "None"
        elif skill_source_mode == "extracted_only":
            final_skills = extracted
            origin = "Extracted from Description" if has_description else "None"
        elif skill_source_mode == "combined":
            final_skills = sorted(set(normalized_source_tags + extracted))
            origin = "Combined (Tags + Extracted)" if (has_source_tags and extracted) else ("Source Tags" if has_source_tags else "Extracted from Description")
        else:  # 'auto'
            if has_source_tags:
                final_skills = normalized_source_tags
                origin = "Source Tags"
            else:
                final_skills = extracted
                origin = "Extracted from Description"

        rows.append({
            "posting_id": idx + 1,
            "title": p["title"],
            "company": p["company"],
            "posted_at": p["posted_at"],
            "description": p["description"],
            "skills_raw": p["skills_raw"],
            "skills_extracted": extracted,
            "skills": final_skills,
            "skill_count": len(final_skills),
            "skill_origin": origin,
            "has_description": has_description,
            "has_source_tags": has_source_tags,
        })

    return pd.DataFrame(rows)


def skill_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate skill demand frequency and percentages across the provided DataFrame.
    """
    if df.empty:
        return pd.DataFrame(columns=["rank", "skill", "category", "postings_mentioning", "pct_of_postings"])

    all_skills = list(itertools.chain.from_iterable(df["skills"]))
    if not all_skills:
        return pd.DataFrame(columns=["rank", "skill", "category", "postings_mentioning", "pct_of_postings"])

    counts = Counter(all_skills)
    total_postings = len(df)

    freq_rows = []
    for rank, (skill, count) in enumerate(counts.most_common(), start=1):
        pct = round(100.0 * count / total_postings, 1)
        cat = get_category_for_skill(skill)
        freq_rows.append({
            "rank": rank,
            "skill": skill,
            "category": cat,
            "postings_mentioning": count,
            "pct_of_postings": pct,
        })

    return pd.DataFrame(freq_rows)


def skill_cooccurrence(df: pd.DataFrame, top_n: int = 15, min_cooc: int = 1) -> pd.DataFrame:
    """
    Calculate co-occurrence frequency between pairs of top skills.
    Only computes when enough postings and skills exist.
    """
    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=["skill_a", "skill_b", "category_a", "category_b", "co_occurrences", "pct_of_postings"])

    all_skills = list(itertools.chain.from_iterable(df["skills"]))
    if not all_skills:
        return pd.DataFrame(columns=["skill_a", "skill_b", "category_a", "category_b", "co_occurrences", "pct_of_postings"])

    top_skills = [s for s, _ in Counter(all_skills).most_common(top_n)]
    top_skills_set = set(top_skills)

    pair_counts = Counter()
    for skills in df["skills"]:
        present = sorted([s for s in set(skills) if s in top_skills_set])
        for a, b in itertools.combinations(present, 2):
            pair_counts[(a, b)] += 1

    total_postings = len(df)
    cooc_rows = []
    for (a, b), count in pair_counts.most_common():
        if count >= min_cooc:
            pct = round(100.0 * count / total_postings, 1)
            cooc_rows.append({
                "skill_a": a,
                "skill_b": b,
                "category_a": get_category_for_skill(a),
                "category_b": get_category_for_skill(b),
                "co_occurrences": count,
                "pct_of_postings": pct,
            })

    return pd.DataFrame(cooc_rows)


def filter_postings(
    df: pd.DataFrame,
    selected_titles: Optional[List[str]] = None,
    keyword: Optional[str] = None,
    selected_companies: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filter DataFrame by title, free-text keyword, or company."""
    if df.empty:
        return df

    filtered = df.copy()

    if selected_titles:
        filtered = filtered[filtered["title"].isin(selected_titles)]

    if selected_companies:
        filtered = filtered[filtered["company"].isin(selected_companies)]

    if keyword and keyword.strip():
        kw = keyword.strip().lower()
        title_match = filtered["title"].str.lower().str.contains(kw, na=False)
        desc_match = filtered["description"].str.lower().str.contains(kw, na=False)
        skills_match = filtered["skills"].apply(lambda skills_list: any(kw in s.lower() for s in skills_list))
        filtered = filtered[title_match | desc_match | skills_match]

    return filtered


def get_postings_for_skill(df: pd.DataFrame, skill_name: str) -> pd.DataFrame:
    """Retrieve all postings that contain a specific skill."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: skill_name in s_list)]


def get_postings_for_pair(df: pd.DataFrame, skill_a: str, skill_b: str) -> pd.DataFrame:
    """Retrieve all postings that contain both skill_a and skill_b."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: (skill_a in s_list) and (skill_b in s_list))]
