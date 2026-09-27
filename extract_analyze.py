"""
Enhanced Extraction & Multi-Dimensional Analysis Engine (v2).

Features:
- Safe regex compilation & boundary lookaheads
- Role Domain & Seniority level classification
- Work Model (Remote / Hybrid / Onsite) detection
- Requirement vs. Preferred skill segmentation
- Role-Skill & Seniority-Skill cross-tabulation matrices
- Skill Gap / Candidate Profile matcher
- In-line HTML description highlighter
- Co-occurrence matrix & Jaccard similarity scoring
"""

import re
import html
import itertools
from collections import Counter
from typing import Dict, List, Optional, Tuple, Any, Set
import pandas as pd

from taxonomy import (
    DEFAULT_SKILL_SYNONYMS,
    SKILL_CATEGORIES,
    get_category_for_skill,
)


def build_regex_pattern(term: str) -> str:
    """
    Build regex pattern with boundary assertions.
    Handles tricky terms like 'c++', 'c#', 'r', 'go', 'ci/cd', '.net'.
    """
    term = term.strip()
    if term.startswith(r"\b") or "(?<=" in term or "(?=" in term:
        return term

    escaped = re.escape(term)
    prefix = r"\b" if re.match(r"^\w", term) else r"(?:^|(?<=[\s,;:(\[\{/]))"
    suffix = r"\b" if re.match(r".*\w$", term) else r"(?:$|(?=[\s,;:.)\]\}/]))"
    return f"{prefix}{escaped}{suffix}"


def compile_taxonomy(taxonomy_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    """Compile dictionary of canonical skill -> list of terms into case-insensitive regex patterns."""
    compiled = {}
    for skill, terms in taxonomy_dict.items():
        if not terms:
            continue
        patterns = [build_regex_pattern(t) for t in terms if t.strip()]
        if patterns:
            compiled[skill] = re.compile("|".join(patterns), re.IGNORECASE)
    return compiled


_DEFAULT_COMPILED = compile_taxonomy(DEFAULT_SKILL_SYNONYMS)


def extract_skills(text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None) -> List[str]:
    """Extract canonical skills from text using compiled taxonomy patterns."""
    if not text or not isinstance(text, str):
        return []

    compiled = compiled_taxonomy if compiled_taxonomy is not None else _DEFAULT_COMPILED
    found = []
    for skill, pattern in compiled.items():
        if pattern.search(text):
            found.append(skill)
    return sorted(set(found))


def extract_skills_with_matches(
    text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None
) -> List[Dict[str, Any]]:
    """Extract skills and return exact text spans for in-line highlighting."""
    if not text or not isinstance(text, str):
        return []

    compiled = compiled_taxonomy if compiled_taxonomy is not None else _DEFAULT_COMPILED
    matches = []
    for skill, pattern in compiled.items():
        for m in pattern.finditer(text):
            matches.append({
                "skill": skill,
                "category": get_category_for_skill(skill),
                "matched_text": m.group(0),
                "start": m.start(),
                "end": m.end(),
            })
    return sorted(matches, key=lambda x: (x["start"], -(x["end"] - x["start"])))


def highlight_skills_in_html(text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None) -> str:
    """
    Produce clean, safe HTML with color-coded highlighted badges for all detected skills in the description.
    """
    if not text or not isinstance(text, str):
        return "<p><em>No description text available.</em></p>"

    matches = extract_skills_with_matches(text, compiled_taxonomy)
    if not matches:
        return f"<div style='line-height:1.6; white-space:pre-wrap;'>{html.escape(text)}</div>"

    # Merge non-overlapping spans
    merged_spans = []
    last_end = -1
    for m in matches:
        if m["start"] >= last_end:
            merged_spans.append(m)
            last_end = m["end"]

    # Build HTML fragments
    html_parts = []
    cursor = 0
    for span in merged_spans:
        if span["start"] > cursor:
            html_parts.append(html.escape(text[cursor:span["start"]]))
        
        matched_str = html.escape(text[span["start"]:span["end"]])
        skill_name = html.escape(span["skill"])
        cat = span["category"]
        
        # Category-based color tint
        color_map = {
            "Programming Languages": ("#DBEAFE", "#1E40AF"),
            "Data Science & AI": ("#FCE7F3", "#9D174D"),
            "Data Engineering": ("#FEF3C7", "#92400E"),
            "Databases & Storage": ("#E0E7FF", "#3730A3"),
            "Cloud & DevOps": ("#DCFCE7", "#166534"),
            "Web & Backend": ("#E0F2FE", "#0369A1"),
            "BI & Analytics": ("#F3E8FF", "#6B21A8"),
            "Practices & Soft Skills": ("#F1F5F9", "#334155"),
        }
        bg, text_col = color_map.get(cat, ("#FEF9C3", "#854D0E"))
        
        tag_html = (
            f"<mark style='background-color:{bg}; color:{text_col}; font-weight:600; "
            f"padding:2px 6px; border-radius:4px; border:1px solid rgba(0,0,0,0.1);' "
            f"title='Detected: {skill_name} ({cat})'>{matched_str}</mark>"
        )
        html_parts.append(tag_html)
        cursor = span["end"]

    if cursor < len(text):
        html_parts.append(html.escape(text[cursor:]))

    return f"<div style='line-height:1.7; white-space:pre-wrap; font-size:0.92rem;'>{''.join(html_parts)}</div>"


def infer_seniority_level(title: str, description: str = "") -> str:
    """Infer experience/seniority level from job title and description text."""
    combined = f"{title} {description}".lower()
    
    if re.search(r"\b(intern|internship|co-op|apprentice|student)\b", combined):
        return "Intern / Entry"
    if re.search(r"\b(junior|jr\.?|associate|entry level|graduate|new grad|lvl 1|level 1)\b", combined):
        return "Junior / Associate"
    if re.search(r"\b(principal|staff|distinguished|director|head of|vp|architect)\b", combined):
        return "Lead / Staff / Architect"
    if re.search(r"\b(senior|sr\.?|lead|tech lead|manager)\b", combined):
        return "Senior / Lead"
    return "Mid-Level / Unspecified"


def infer_role_domain(title: str) -> str:
    """Classify posting into a technical role domain based on title keywords."""
    t = title.lower()
    
    if re.search(r"\b(data scientist|data science|machine learning|ml engineer|deep learning|ai engineer|ai researcher|nlp engineer|computer vision|llm)\b", t):
        return "Data Science & AI"
    if re.search(r"\b(data engineer|big data|etl|analytics engineer|data architect|database admin|dba)\b", t):
        return "Data Engineering"
    if re.search(r"\b(data analyst|business intelligence|bi analyst|bi developer|analytics analyst|reporting)\b", t):
        return "BI & Analytics"
    if re.search(r"\b(devops|sre|site reliability|cloud engineer|platform engineer|infrastructure|sysadmin|systems engineer)\b", t):
        return "Cloud & DevOps"
    if re.search(r"\b(frontend|front-end|ui engineer|ui developer|web developer|react developer|angular developer)\b", t):
        return "Frontend & Web"
    if re.search(r"\b(backend|back-end|api engineer|java developer|python developer|golang developer|c\+\+ developer)\b", t):
        return "Backend & Systems"
    if re.search(r"\b(full stack|full-stack|software engineer|software developer|swe|application engineer)\b", t):
        return "Full Stack / Software Eng"
    return "Other / General Tech"


def infer_work_model(text: str) -> str:
    """Infer work model (Remote, Hybrid, Onsite) from posting metadata/text."""
    t = text.lower()
    if re.search(r"\b(remote|work from home|telecommute|100% remote|anywhere)\b", t):
        return "Remote"
    if re.search(r"\b(hybrid|flexible work|partial remote)\b", t):
        return "Hybrid"
    if re.search(r"\b(on-site|onsite|in-office|in office)\b", t):
        return "Onsite"
    return "Unspecified"


def segment_requirements_vs_preferred(text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None) -> Tuple[List[str], List[str]]:
    """
    Heuristically segment job description into Must-Have (Required) vs Nice-to-Have (Preferred) skills.
    """
    if not text:
        return [], []

    lines = text.split("\n")
    required_text = []
    preferred_text = []
    current_section = "required"

    for line in lines:
        lower_line = line.lower()
        if re.search(r"\b(preferred|bonus|nice to have|plus|desired|optional|advantageous)\b", lower_line):
            current_section = "preferred"
        elif re.search(r"\b(requirements|qualifications|must have|required|what you bring|experience needed|minimum)\b", lower_line):
            current_section = "required"
        
        if current_section == "preferred":
            preferred_text.append(line)
        else:
            required_text.append(line)

    req_skills = extract_skills("\n".join(required_text), compiled_taxonomy)
    pref_skills = extract_skills("\n".join(preferred_text), compiled_taxonomy)
    # Deduplicate pref from req
    pref_only = [s for s in pref_skills if s not in req_skills]
    return req_skills, pref_only


def normalize_posting(p: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize field names across arbitrary JSON/CSV input schemas."""
    title = p.get("title") or p.get("job_title") or p.get("position") or "Untitled Position"
    company = p.get("company") or p.get("employer_name") or p.get("employer") or p.get("company_name") or "Unknown Company"
    posted_at = p.get("posted_at") or p.get("job_posted_at_datetime_utc") or p.get("dateCreated") or p.get("date") or "N/A"
    country = p.get("country") or p.get("job_country") or p.get("countryCode") or p.get("location") or "N/A"
    
    description = p.get("description") or p.get("job_description") or p.get("summary") or p.get("text") or ""
    if not isinstance(description, str):
        description = "" if pd.isna(description) else str(description)

    skills_raw = p.get("skills_raw") or p.get("skills") or p.get("tags") or p.get("job_skills")
    parsed_skills_raw = []
    if isinstance(skills_raw, list):
        parsed_skills_raw = [str(s).strip() for s in skills_raw if str(s).strip()]
    elif isinstance(skills_raw, str) and skills_raw.strip():
        parsed_skills_raw = [s.strip() for s in re.split(r"[,;|]", skills_raw) if s.strip()]

    return {
        "title": str(title).strip(),
        "company": str(company).strip(),
        "posted_at": str(posted_at).strip(),
        "country": str(country).strip(),
        "description": description.strip(),
        "skills_raw": parsed_skills_raw,
    }


def deduplicate_postings(postings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Deduplicate postings on (title, company, description snippet)."""
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
    skill_source_mode: str = "auto",
) -> pd.DataFrame:
    """Build enriched DataFrame containing skills, seniority, domain, work model, and segmented requirements."""
    compiled = compile_taxonomy(taxonomy_dict) if taxonomy_dict is not None else _DEFAULT_COMPILED
    rows = []

    for idx, raw_p in enumerate(postings):
        p = normalize_posting(raw_p)
        has_source_tags = bool(p["skills_raw"])
        has_description = bool(p["description"])

        extracted = extract_skills(p["description"], compiled_taxonomy=compiled) if has_description else []
        req_skills, pref_skills = segment_requirements_vs_preferred(p["description"], compiled_taxonomy=compiled) if has_description else ([], [])

        normalized_source_tags = []
        if has_source_tags:
            for s in p["skills_raw"]:
                matched = extract_skills(s, compiled_taxonomy=compiled)
                if matched:
                    normalized_source_tags.extend(matched)
                else:
                    normalized_source_tags.append(s)
            normalized_source_tags = sorted(set(normalized_source_tags))

        # Mode Selection
        if skill_source_mode == "source_tags_only":
            final_skills = normalized_source_tags
            origin = "Source Tags" if has_source_tags else "None"
        elif skill_source_mode == "extracted_only":
            final_skills = extracted
            origin = "Extracted from Description" if has_description else "None"
        elif skill_source_mode == "combined":
            final_skills = sorted(set(normalized_source_tags + extracted))
            origin = "Combined (Tags + Extracted)" if (has_source_tags and extracted) else ("Source Tags" if has_source_tags else "Extracted from Description")
        else:  # auto
            if has_source_tags:
                final_skills = normalized_source_tags
                origin = "Source Tags"
            else:
                final_skills = extracted
                origin = "Extracted from Description"

        seniority = infer_seniority_level(p["title"], p["description"])
        domain = infer_role_domain(p["title"])
        work_model = infer_work_model(f"{p['title']} {p['country']} {p['description']}")

        rows.append({
            "posting_id": idx + 1,
            "title": p["title"],
            "company": p["company"],
            "country": p["country"],
            "posted_at": p["posted_at"],
            "seniority": seniority,
            "role_domain": domain,
            "work_model": work_model,
            "description": p["description"],
            "skills_raw": p["skills_raw"],
            "skills_extracted": extracted,
            "skills_required": req_skills,
            "skills_preferred": pref_skills,
            "skills": final_skills,
            "skill_count": len(final_skills),
            "skill_origin": origin,
            "has_description": has_description,
            "has_source_tags": has_source_tags,
        })

    return pd.DataFrame(rows)


def skill_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate skill frequencies, percentages, and category metadata."""
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
    """Calculate co-occurrences and Jaccard similarity between top skills."""
    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=["skill_a", "skill_b", "category_a", "category_b", "co_occurrences", "pct_of_postings", "jaccard_similarity"])

    all_skills = list(itertools.chain.from_iterable(df["skills"]))
    if not all_skills:
        return pd.DataFrame(columns=["skill_a", "skill_b", "category_a", "category_b", "co_occurrences", "pct_of_postings", "jaccard_similarity"])

    individual_counts = Counter(all_skills)
    top_skills = [s for s, _ in individual_counts.most_common(top_n)]
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
            # Jaccard = Intersection / Union = count / (count_a + count_b - count)
            union = individual_counts[a] + individual_counts[b] - count
            jaccard = round(count / union, 2) if union > 0 else 0.0

            cooc_rows.append({
                "skill_a": a,
                "skill_b": b,
                "category_a": get_category_for_skill(a),
                "category_b": get_category_for_skill(b),
                "co_occurrences": count,
                "pct_of_postings": pct,
                "jaccard_similarity": jaccard,
            })

    return pd.DataFrame(cooc_rows)


def role_skill_cross_tab(df: pd.DataFrame, top_k_skills: int = 10) -> pd.DataFrame:
    """Compute role domain vs skill frequency cross-tabulation."""
    if df.empty:
        return pd.DataFrame()

    freq = skill_frequency(df)
    if freq.empty:
        return pd.DataFrame()

    top_skills = freq.head(top_k_skills)["skill"].tolist()
    records = []

    for _, row in df.iterrows():
        domain = row["role_domain"]
        for s in row["skills"]:
            if s in top_skills:
                records.append({"role_domain": domain, "skill": s})

    if not records:
        return pd.DataFrame()

    temp_df = pd.DataFrame(records)
    ct = pd.crosstab(temp_df["role_domain"], temp_df["skill"])
    return ct


def seniority_skill_cross_tab(df: pd.DataFrame, top_k_skills: int = 10) -> pd.DataFrame:
    """Compute seniority vs skill frequency cross-tabulation."""
    if df.empty:
        return pd.DataFrame()

    freq = skill_frequency(df)
    if freq.empty:
        return pd.DataFrame()

    top_skills = freq.head(top_k_skills)["skill"].tolist()
    records = []

    for _, row in df.iterrows():
        sen = row["seniority"]
        for s in row["skills"]:
            if s in top_skills:
                records.append({"seniority": sen, "skill": s})

    if not records:
        return pd.DataFrame()

    temp_df = pd.DataFrame(records)
    ct = pd.crosstab(temp_df["seniority"], temp_df["skill"])
    return ct


def calculate_skill_gap(
    df: pd.DataFrame, user_skills: List[str]
) -> Dict[str, Any]:
    """
    Compare candidate's skill profile against the dataset.
    Returns match metrics, qualified postings percentage, and high-impact missing skills.
    """
    if df.empty or not user_skills:
        return {
            "total_postings": len(df),
            "user_skill_count": len(user_skills),
            "match_rate_50pct": 0.0,
            "match_rate_80pct": 0.0,
            "missing_skills_ranked": [],
        }

    user_skills_set = set(s.strip().lower() for s in user_skills if s.strip())
    postings_count = len(df)
    matches_50 = 0
    matches_80 = 0
    missing_skill_counter = Counter()

    for _, row in df.iterrows():
        job_skills = row["skills"]
        if not job_skills:
            continue
        
        job_skills_lower = [s.lower() for s in job_skills]
        shared = [s for s in job_skills_lower if s in user_skills_set]
        coverage = len(shared) / len(job_skills)

        if coverage >= 0.50:
            matches_50 += 1
        if coverage >= 0.80:
            matches_80 += 1

        for js in job_skills:
            if js.lower() not in user_skills_set:
                missing_skill_counter[js] += 1

    missing_ranked = [
        {
            "skill": skill,
            "category": get_category_for_skill(skill),
            "job_mentions": count,
            "pct_unlockable": round(100.0 * count / postings_count, 1),
        }
        for skill, count in missing_skill_counter.most_common(12)
    ]

    return {
        "total_postings": postings_count,
        "user_skill_count": len(user_skills),
        "match_rate_50pct": round(100.0 * matches_50 / max(1, postings_count), 1),
        "match_rate_80pct": round(100.0 * matches_80 / max(1, postings_count), 1),
        "missing_skills_ranked": missing_ranked,
    }


def filter_postings(
    df: pd.DataFrame,
    selected_titles: Optional[List[str]] = None,
    keyword: Optional[str] = None,
    selected_companies: Optional[List[str]] = None,
    selected_seniorities: Optional[List[str]] = None,
    selected_domains: Optional[List[str]] = None,
    selected_work_models: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Multi-dimensional filtering for postings DataFrame."""
    if df.empty:
        return df

    filtered = df.copy()

    if selected_titles:
        filtered = filtered[filtered["title"].isin(selected_titles)]

    if selected_companies:
        filtered = filtered[filtered["company"].isin(selected_companies)]

    if selected_seniorities:
        filtered = filtered[filtered["seniority"].isin(selected_seniorities)]

    if selected_domains:
        filtered = filtered[filtered["role_domain"].isin(selected_domains)]

    if selected_work_models:
        filtered = filtered[filtered["work_model"].isin(selected_work_models)]

    if keyword and keyword.strip():
        kw = keyword.strip().lower()
        title_match = filtered["title"].str.lower().str.contains(kw, na=False)
        desc_match = filtered["description"].str.lower().str.contains(kw, na=False)
        skills_match = filtered["skills"].apply(lambda skills_list: any(kw in s.lower() for s in skills_list))
        filtered = filtered[title_match | desc_match | skills_match]

    return filtered


def get_postings_for_skill(df: pd.DataFrame, skill_name: str) -> pd.DataFrame:
    """Retrieve postings matching a specific skill."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: skill_name in s_list)]


def get_postings_for_pair(df: pd.DataFrame, skill_a: str, skill_b: str) -> pd.DataFrame:
    """Retrieve postings matching both skill_a and skill_b."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: (skill_a in s_list) and (skill_b in s_list))]
