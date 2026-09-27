"""
Comprehensive Multi-Dimensional Analytics Engine v3.0.

Features:
- Safe regex compilation & boundary lookaheads (180+ skills)
- Salary & Compensation parser (Min, Max, Avg, Currency, Annualization)
- Years of Experience & Education Requirement extractor
- Section context segmentation (Required vs Preferred skills)
- Weighted Demand Score calculation
- A/B Cohort Comparison Engine (e.g. Remote vs Onsite, Senior vs Junior)
- Structured Career Learning Roadmap generator
- Salary by Skill Leaderboard calculator
- In-line HTML description highlighter with tooltips
- Co-occurrence with Jaccard correlation scoring
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
    """Build regex pattern with boundary assertions for complex tokens."""
    term = term.strip()
    if term.startswith(r"\b") or "(?<=" in term or "(?=" in term:
        return term

    escaped = re.escape(term)
    prefix = r"\b" if re.match(r"^\w", term) else r"(?:^|(?<=[\s,;:(\[\{/]))"
    suffix = r"\b" if re.match(r".*\w$", term) else r"(?:$|(?=[\s,;:.)\]\}/]))"
    return f"{prefix}{escaped}{suffix}"


def compile_taxonomy(taxonomy_dict: Dict[str, List[str]]) -> Dict[str, re.Pattern]:
    """Compile dictionary of canonical skills into case-insensitive regex patterns."""
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
    """Produce clean, safe HTML with color-coded highlighted badges for detected skills."""
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

    html_parts = []
    cursor = 0
    color_map = {
        "Programming Languages": ("#DBEAFE", "#1E40AF"),
        "Data Science & AI": ("#FCE7F3", "#9D174D"),
        "Data Engineering": ("#FEF3C7", "#92400E"),
        "Databases & Storage": ("#E0E7FF", "#3730A3"),
        "Cloud & DevOps": ("#DCFCE7", "#166534"),
        "Web & Frontend": ("#E0F2FE", "#0369A1"),
        "Web & Backend": ("#CCFBF1", "#115E59"),
        "Mobile Development": ("#FDE047", "#854D0E"),
        "Cybersecurity & Security": ("#FEE2E2", "#991B1B"),
        "BI & Analytics": ("#F3E8FF", "#6B21A8"),
        "Practices & Soft Skills": ("#F1F5F9", "#334155"),
    }

    for span in merged_spans:
        if span["start"] > cursor:
            html_parts.append(html.escape(text[cursor:span["start"]]))

        matched_str = html.escape(text[span["start"]:span["end"]])
        skill_name = html.escape(span["skill"])
        cat = span["category"]
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


def extract_salary_info(text: str) -> Dict[str, Any]:
    """
    Extract compensation range, currency, and period from posting text or metadata.
    Handles forms like: $120,000 - $160,000, $120k - $150k, 80k-100k USD, £60,000 - £80,000, $50-70/hr.
    Annualizes hourly wages assuming 2,080 work hours/year.
    """
    if not text:
        return {"has_salary": False, "salary_min": None, "salary_max": None, "salary_avg": None, "currency": "$", "period": "yearly"}

    # Pattern for ranges with $ or £ or €
    # e.g., $120k - $160k, $120,000 - $160,000, 120,000 - 150,000 USD, $50 - $80 / hr
    pat_range = re.search(
        r"([$£€]?)\s*(\d{2,3}(?:,\d{3})*|\d{2,3})\s*(?:k|K)?\s*(?:-|to|–)\s*([$£€]?)\s*(\d{2,3}(?:,\d{3})*|\d{2,3})\s*(k|K)?\s*(usd|eur|gbp)?\s*(?:/|\s*per\s*)?\s*(yr|year|annual|annually|hr|hour|hourly)?",
        text,
        re.IGNORECASE,
    )

    if pat_range:
        curr_symbol = pat_range.group(1) or pat_range.group(3) or "$"
        raw_min = pat_range.group(2).replace(",", "")
        raw_max = pat_range.group(4).replace(",", "")
        has_k = bool(pat_range.group(5) or "k" in pat_range.group(0).lower())
        period_str = (pat_range.group(7) or "").lower()
        is_hourly = any(h in period_str or "hr" in pat_range.group(0).lower() or "hour" in pat_range.group(0).lower() for h in ["hr", "hour", "hourly"])

        try:
            val_min = float(raw_min)
            val_max = float(raw_max)

            # Check if numbers are in thousands (e.g. 120 means 120k if > 25 and not hourly)
            if not is_hourly:
                if has_k or val_min < 1000:
                    val_min = val_min * 1000 if val_min < 1000 else val_min
                    val_max = val_max * 1000 if val_max < 1000 else val_max
            else:
                # Annualize hourly rate
                val_min = val_min * 2080
                val_max = val_max * 2080

            if 20000 <= val_min <= 600000 and 20000 <= val_max <= 600000 and val_min <= val_max:
                avg_val = round((val_min + val_max) / 2.0, 0)
                return {
                    "has_salary": True,
                    "salary_min": int(val_min),
                    "salary_max": int(val_max),
                    "salary_avg": int(avg_val),
                    "currency": curr_symbol if curr_symbol in ["$", "£", "€"] else "$",
                    "period": "yearly",
                }
        except (ValueError, TypeError):
            pass

    return {"has_salary": False, "salary_min": None, "salary_max": None, "salary_avg": None, "currency": "$", "period": "yearly"}


def extract_years_of_experience(text: str) -> Optional[int]:
    """Extract minimum years of experience required from posting text."""
    if not text:
        return None

    # Matches: 3+ years, 5-7 years, minimum 2 years, 4+ yrs
    m = re.search(r"(\d+)(?:\s*(?:-|to|–|\+)\s*\d+)?\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+of\s+experience)?", text, re.IGNORECASE)
    if m:
        try:
            val = int(m.group(1))
            if 0 <= val <= 20:
                return val
        except ValueError:
            pass
    return None


def extract_education_level(text: str) -> str:
    """Extract minimum degree qualification requirement."""
    if not text:
        return "Not Specified"
    t = text.lower()
    if re.search(r"\b(ph\.?d\.?|doctorate)\b", t):
        return "PhD / Doctorate"
    if re.search(r"\b(master'?s|ms|m\.s\.|msc|m\.sc\.)\b", t):
        return "Master's Degree"
    if re.search(r"\b(bachelor'?s|bs|b\.s\.|bsc|b\.sc\.|b\.tech|undergraduate)\b", t):
        return "Bachelor's Degree"
    if re.search(r"\b(bootcamp|self-taught|equivalent experience)\b", t):
        return "Bootcamp / Self-Taught"
    return "Not Specified"


def infer_seniority_level(title: str, description: str = "") -> str:
    """Infer experience/seniority level from job title and description."""
    combined = f"{title} {description}".lower()
    if re.search(r"\b(intern|internship|co-op|apprentice|student)\b", combined):
        return "Intern / Entry"
    if re.search(r"\b(junior|jr\.?|associate|entry level|graduate|new grad|lvl 1|level 1)\b", combined):
        return "Junior / Associate"
    if re.search(r"\b(principal|staff|distinguished|director|head of|vp|architect)\b", combined):
        return "Lead / Staff / Architect"
    if re.search(r"\b(senior|sr\.?|lead|tech lead|manager)\b", combined):
        return "Senior / Lead"
    return "Mid-Level"


def infer_role_domain(title: str) -> str:
    """Classify posting into a technical role domain."""
    t = title.lower()
    if re.search(r"\b(data scientist|data science|machine learning|ml engineer|deep learning|ai engineer|ai researcher|nlp engineer|computer vision|llm|genai)\b", t):
        return "Data Science & AI"
    if re.search(r"\b(data engineer|big data|etl|analytics engineer|data architect|database admin|dba)\b", t):
        return "Data Engineering"
    if re.search(r"\b(data analyst|business intelligence|bi analyst|bi developer|analytics analyst|reporting)\b", t):
        return "BI & Analytics"
    if re.search(r"\b(devops|sre|site reliability|cloud engineer|platform engineer|infrastructure|sysadmin|systems engineer)\b", t):
        return "Cloud & DevOps"
    if re.search(r"\b(security|cybersecurity|infosec|appsec|soc analyst|penetration)\b", t):
        return "Cybersecurity"
    if re.search(r"\b(mobile|ios|android|flutter|react native|swift developer|kotlin developer)\b", t):
        return "Mobile Development"
    if re.search(r"\b(frontend|front-end|ui engineer|ui developer|web developer|react developer|angular developer|vue developer)\b", t):
        return "Frontend & Web"
    if re.search(r"\b(backend|back-end|api engineer|java developer|python developer|golang developer|c\+\+ developer|rust developer)\b", t):
        return "Backend & Systems"
    if re.search(r"\b(full stack|full-stack|software engineer|software developer|swe|application engineer)\b", t):
        return "Full Stack / Software Eng"
    return "Other Tech Roles"


def infer_work_model(text: str) -> str:
    """Infer work model (Remote, Hybrid, Onsite)."""
    t = text.lower()
    if re.search(r"\b(remote|work from home|telecommute|100% remote|anywhere)\b", t):
        return "Remote"
    if re.search(r"\b(hybrid|flexible work|partial remote)\b", t):
        return "Hybrid"
    if re.search(r"\b(on-site|onsite|in-office|in office)\b", t):
        return "Onsite"
    return "Unspecified"


def segment_requirements_vs_preferred(text: str, compiled_taxonomy: Optional[Dict[str, re.Pattern]] = None) -> Tuple[List[str], List[str]]:
    """Segment job description into Must-Have (Required) vs Nice-to-Have (Preferred) skills."""
    if not text:
        return [], []

    lines = text.split("\n")
    required_text = []
    preferred_text = []
    current_section = "required"

    for line in lines:
        lower_line = line.lower()
        if re.search(r"\b(preferred|bonus|nice to have|plus|desired|optional|advantageous|great to have)\b", lower_line):
            current_section = "preferred"
        elif re.search(r"\b(requirements|qualifications|must have|required|what you bring|experience needed|minimum requirements)\b", lower_line):
            current_section = "required"

        if current_section == "preferred":
            preferred_text.append(line)
        else:
            required_text.append(line)

    req_skills = extract_skills("\n".join(required_text), compiled_taxonomy)
    pref_skills = extract_skills("\n".join(preferred_text), compiled_taxonomy)
    pref_only = [s for s in pref_skills if s not in req_skills]
    return req_skills, pref_only


def normalize_posting(p: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize field names across arbitrary input schemas."""
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

    # Salary extraction directly if fields present
    salary_direct = p.get("salary") or p.get("compensation") or p.get("salary_range")

    return {
        "title": str(title).strip(),
        "company": str(company).strip(),
        "posted_at": str(posted_at).strip(),
        "country": str(country).strip(),
        "description": description.strip(),
        "skills_raw": parsed_skills_raw,
        "salary_field": str(salary_direct) if salary_direct else "",
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
    """Build enriched DataFrame containing skills, salary, experience, education, seniority, and domain."""
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

        # Rich dimension extraction
        combined_text = f"{p['salary_field']} {p['description']}"
        sal_info = extract_salary_info(combined_text)
        exp_years = extract_years_of_experience(p["description"])
        education = extract_education_level(p["description"])

        rows.append({
            "posting_id": idx + 1,
            "title": p["title"],
            "company": p["company"],
            "country": p["country"],
            "posted_at": p["posted_at"],
            "seniority": seniority,
            "role_domain": domain,
            "work_model": work_model,
            "has_salary": sal_info["has_salary"],
            "salary_min": sal_info["salary_min"],
            "salary_max": sal_info["salary_max"],
            "salary_avg": sal_info["salary_avg"],
            "salary_currency": sal_info["currency"],
            "min_years_experience": exp_years,
            "education_level": education,
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
    """Calculate raw frequency and weighted demand score (Required = 1.0, Preferred = 0.5)."""
    if df.empty:
        return pd.DataFrame(columns=["rank", "skill", "category", "postings_mentioning", "pct_of_postings", "weighted_score"])

    all_skills = list(itertools.chain.from_iterable(df["skills"]))
    if not all_skills:
        return pd.DataFrame(columns=["rank", "skill", "category", "postings_mentioning", "pct_of_postings", "weighted_score"])

    counts = Counter(all_skills)
    total_postings = len(df)

    # Weighted calculation
    weighted_scores = Counter()
    for _, row in df.iterrows():
        reqs = set(row.get("skills_required", []))
        prefs = set(row.get("skills_preferred", []))
        for s in row["skills"]:
            if s in reqs:
                weighted_scores[s] += 1.0
            elif s in prefs:
                weighted_scores[s] += 0.5
            else:
                weighted_scores[s] += 0.8  # neutral/unsegmented mention

    freq_rows = []
    for rank, (skill, count) in enumerate(counts.most_common(), start=1):
        pct = round(100.0 * count / total_postings, 1)
        w_score = round(weighted_scores[skill], 1)
        cat = get_category_for_skill(skill)
        freq_rows.append({
            "rank": rank,
            "skill": skill,
            "category": cat,
            "postings_mentioning": count,
            "pct_of_postings": pct,
            "weighted_score": w_score,
        })

    return pd.DataFrame(freq_rows)


def skill_cooccurrence(df: pd.DataFrame, top_n: int = 15, min_cooc: int = 1) -> pd.DataFrame:
    """Calculate co-occurrences and Jaccard correlation between top skills."""
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


def calculate_salary_by_skill(df: pd.DataFrame, top_k_skills: int = 12) -> pd.DataFrame:
    """Calculate average and median annual compensation for top skills."""
    df_sal = df[df["has_salary"] & df["salary_avg"].notna()].copy()
    if df_sal.empty:
        return pd.DataFrame(columns=["skill", "category", "postings_with_salary", "avg_salary", "min_salary", "max_salary"])

    freq = skill_frequency(df)
    if freq.empty:
        return pd.DataFrame()

    top_skills = freq.head(top_k_skills)["skill"].tolist()
    skill_salaries = []

    for s in top_skills:
        matching = df_sal[df_sal["skills"].apply(lambda sl: s in sl)]
        if len(matching) >= 1:
            avg_s = int(matching["salary_avg"].mean())
            min_s = int(matching["salary_min"].min())
            max_s = int(matching["salary_max"].max())
            skill_salaries.append({
                "skill": s,
                "category": get_category_for_skill(s),
                "postings_with_salary": len(matching),
                "avg_salary": avg_s,
                "min_salary": min_s,
                "max_salary": max_s,
            })

    res = pd.DataFrame(skill_salaries)
    if not res.empty:
        res = res.sort_values(by="avg_salary", ascending=False)
    return res


def compare_cohorts(
    df: pd.DataFrame,
    cohort_col: str,
    cohort_a_val: str,
    cohort_b_val: str,
    top_n: int = 12,
) -> pd.DataFrame:
    """
    Compare skill demand between two cohorts (e.g., Remote vs Onsite, Senior vs Junior).
    Returns comparative prevalence and relative percentage difference.
    """
    if df.empty or cohort_col not in df.columns:
        return pd.DataFrame()

    df_a = df[df[cohort_col] == cohort_a_val]
    df_b = df[df[cohort_col] == cohort_b_val]

    if df_a.empty or df_b.empty:
        return pd.DataFrame()

    freq_a = skill_frequency(df_a).set_index("skill")["pct_of_postings"].to_dict()
    freq_b = skill_frequency(df_b).set_index("skill")["pct_of_postings"].to_dict()

    all_compared_skills = sorted(list(set(list(freq_a.keys()) + list(freq_b.keys()))))
    comparison_rows = []

    for s in all_compared_skills:
        pct_a = freq_a.get(s, 0.0)
        pct_b = freq_b.get(s, 0.0)
        diff = round(pct_a - pct_b, 1)
        # Skip if both are very low
        if pct_a >= 5.0 or pct_b >= 5.0:
            comparison_rows.append({
                "skill": s,
                "category": get_category_for_skill(s),
                f"pct_{cohort_a_val}": pct_a,
                f"pct_{cohort_b_val}": pct_b,
                "diff_a_minus_b": diff,
                "total_demand": pct_a + pct_b,
            })

    res = pd.DataFrame(comparison_rows)
    if not res.empty:
        res = res.sort_values(by="total_demand", ascending=False).head(top_n)
    return res


def generate_career_roadmap(
    df: pd.DataFrame,
    current_skills: List[str],
    target_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a 4-Phase Structured Learning Roadmap to transition or advance into a target domain.
    Prioritizes skills by market frequency and dependency hierarchy.
    """
    target_df = df if not target_domain or target_domain == "All Roles" else df[df["role_domain"] == target_domain]
    if target_df.empty:
        target_df = df

    freq = skill_frequency(target_df)
    user_set = set(s.lower().strip() for s in current_skills)

    missing_skills = []
    for _, r in freq.iterrows():
        if r["skill"].lower() not in user_set:
            missing_skills.append({
                "skill": r["skill"],
                "category": r["category"],
                "pct_of_jobs": r["pct_of_postings"],
                "postings_count": r["postings_mentioning"],
            })

    # Group into 4 Structured Milestones
    phase1 = []  # Core Languages & Foundation
    phase2 = []  # Primary Frameworks & Engineering
    phase3 = []  # Cloud, Scale & MLOps/Data Infra
    phase4 = []  # Advanced Systems & Leadership

    for s in missing_skills[:16]:
        cat = s["category"]
        if cat in ["Programming Languages", "Databases & Storage"]:
            phase1.append(s)
        elif cat in ["Data Science & AI", "Web & Frontend", "Web & Backend", "BI & Analytics"]:
            phase2.append(s)
        elif cat in ["Data Engineering", "Cloud & DevOps", "Mobile Development"]:
            phase3.append(s)
        else:
            phase4.append(s)

    return {
        "target_domain": target_domain or "General Tech",
        "postings_evaluated": len(target_df),
        "user_skill_count": len(current_skills),
        "missing_count": len(missing_skills),
        "phases": {
            "Phase 1: Core Foundation & Data Layer": phase1,
            "Phase 2: Primary Frameworks & Core Stack": phase2,
            "Phase 3: Cloud, Scale & Data Infrastructure": phase3,
            "Phase 4: Advanced Systems & Leadership Practices": phase4,
        },
    }


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
    return pd.crosstab(temp_df["role_domain"], temp_df["skill"])


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
    return pd.crosstab(temp_df["seniority"], temp_df["skill"])


def calculate_skill_gap(
    df: pd.DataFrame, user_skills: List[str]
) -> Dict[str, Any]:
    """Calculate profile match rates and ROI ranking of missing skills."""
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
    selected_educations: Optional[List[str]] = None,
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

    if selected_educations:
        filtered = filtered[filtered["education_level"].isin(selected_educations)]

    if keyword and keyword.strip():
        kw = keyword.strip().lower()
        title_match = filtered["title"].str.lower().str.contains(kw, na=False)
        desc_match = filtered["description"].str.lower().str.contains(kw, na=False)
        skills_match = filtered["skills"].apply(lambda skills_list: any(kw in s.lower() for s in skills_list))
        filtered = filtered[title_match | desc_match | skills_match]

    return filtered


def get_postings_for_skill(df: pd.DataFrame, skill_name: str) -> pd.DataFrame:
    """Retrieve postings containing a specific skill."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: skill_name in s_list)]


def get_postings_for_pair(df: pd.DataFrame, skill_a: str, skill_b: str) -> pd.DataFrame:
    """Retrieve postings containing both skill_a and skill_b."""
    if df.empty:
        return df
    return df[df["skills"].apply(lambda s_list: (skill_a in s_list) and (skill_b in s_list))]
