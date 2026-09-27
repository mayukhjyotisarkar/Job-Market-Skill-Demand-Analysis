"""
Comprehensive test suite for Job Market Skill Demand Analyzer (v2.0).
"""

import json
import os
import pandas as pd
from taxonomy import (
    get_default_taxonomy,
    get_category_for_skill,
    TAXONOMY_PRESETS,
)
from extract_analyze import (
    extract_skills,
    extract_skills_with_matches,
    highlight_skills_in_html,
    infer_seniority_level,
    infer_role_domain,
    infer_work_model,
    deduplicate_postings,
    build_skill_frame,
    skill_frequency,
    skill_cooccurrence,
    role_skill_cross_tab,
    seniority_skill_cross_tab,
    calculate_skill_gap,
    filter_postings,
    get_postings_for_skill,
    get_postings_for_pair,
)


def test_v2_taxonomy_and_boundaries():
    text = (
        "Seeking a Senior Data Scientist proficient in Python, SQL, PyTorch, LangChain, "
        "and Docker on AWS with Kubernetes. Experience with C++, C#, and Go microservices."
    )
    skills = extract_skills(text)
    expected = ["Python", "SQL", "PyTorch", "LangChain", "Docker", "AWS", "Kubernetes", "C++", "C#", "Go", "Microservices"]
    for exp in expected:
        assert exp in skills, f"Missing expected skill: {exp} in {skills}"
    print("[PASS] test_v2_taxonomy_and_boundaries passed")


def test_seniority_and_domain_inference():
    # Seniority tests
    assert infer_seniority_level("Junior Data Analyst Intern") in ["Intern / Entry", "Junior / Associate"]
    assert infer_seniority_level("Senior Machine Learning Engineer") == "Senior / Lead"
    assert infer_seniority_level("Staff Backend Architect") == "Lead / Staff / Architect"

    # Domain tests
    assert infer_role_domain("Senior Data Scientist") == "Data Science & AI"
    assert infer_role_domain("Lead Data Engineer (Spark & AWS)") == "Data Engineering"
    assert infer_role_domain("Frontend React Developer") == "Frontend & Web"
    assert infer_role_domain("DevOps / SRE Engineer") == "Cloud & DevOps"
    print("[PASS] test_seniority_and_domain_inference passed")


def test_html_highlighter():
    desc = "We require Python and SQL for machine learning pipelines."
    html_out = highlight_skills_in_html(desc)
    assert "<mark" in html_out
    assert "Python" in html_out
    print("[PASS] test_html_highlighter passed")


def test_pipeline_on_v2_sample():
    with open("sample_postings.json", "r", encoding="utf-8") as f:
        postings = json.load(f)

    assert len(postings) == 25, f"Expected 25 sample postings, got {len(postings)}"

    df = build_skill_frame(postings)
    assert len(df) == 25
    assert "seniority" in df.columns
    assert "role_domain" in df.columns
    assert "work_model" in df.columns

    # Frequency
    freq = skill_frequency(df)
    assert not freq.empty
    assert "Python" in freq["skill"].values

    # Cross-tabulations
    role_ct = role_skill_cross_tab(df, top_k_skills=5)
    assert not role_ct.empty

    sen_ct = seniority_skill_cross_tab(df, top_k_skills=5)
    assert not sen_ct.empty

    # Co-occurrence
    cooc = skill_cooccurrence(df, top_n=10)
    assert not cooc.empty
    assert "jaccard_similarity" in cooc.columns

    # Skill Gap Matcher
    user_skills = ["Python", "SQL", "Git"]
    gap = calculate_skill_gap(df, user_skills)
    assert gap["user_skill_count"] == 3
    assert len(gap["missing_skills_ranked"]) > 0
    print("[PASS] test_pipeline_on_v2_sample passed")


if __name__ == "__main__":
    test_v2_taxonomy_and_boundaries()
    test_seniority_and_domain_inference()
    test_html_highlighter()
    test_pipeline_on_v2_sample()
    print("\nALL V2 TESTS PASSED SUCCESSFULLY!")
