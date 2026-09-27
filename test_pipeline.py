"""
Comprehensive test suite for Job Market Skill Demand Analyzer (v3.0 Enterprise Edition).
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
    extract_salary_info,
    extract_years_of_experience,
    extract_education_level,
    infer_seniority_level,
    infer_role_domain,
    infer_work_model,
    deduplicate_postings,
    build_skill_frame,
    skill_frequency,
    skill_cooccurrence,
    calculate_salary_by_skill,
    compare_cohorts,
    generate_career_roadmap,
    role_skill_cross_tab,
    seniority_skill_cross_tab,
    calculate_skill_gap,
    filter_postings,
    get_postings_for_skill,
    get_postings_for_pair,
)


def test_v3_salary_extraction():
    # Test annual range
    s1 = extract_salary_info("The compensation is $130,000 - $175,000 per year plus bonus.")
    assert s1["has_salary"] is True
    assert s1["salary_min"] == 130000
    assert s1["salary_max"] == 175000
    assert s1["salary_avg"] == 152500

    # Test 'k' notation
    s2 = extract_salary_info("Salary: 140k - 190k USD.")
    assert s2["has_salary"] is True
    assert s2["salary_min"] == 140000
    assert s2["salary_max"] == 190000

    # Test hourly rate annualization
    s3 = extract_salary_info("Pay rate is $60 - $80 / hr.")
    assert s3["has_salary"] is True
    assert s3["salary_min"] == int(60 * 2080)
    assert s3["salary_max"] == int(80 * 2080)
    print("[PASS] test_v3_salary_extraction passed")


def test_v3_experience_and_education():
    t1 = "Requires 5+ years of experience with distributed systems and a Master's Degree in CS."
    assert extract_years_of_experience(t1) == 5
    assert extract_education_level(t1) == "Master's Degree"

    t2 = "Looking for someone with 3-5 years experience and a Bachelor's Degree."
    assert extract_years_of_experience(t2) == 3
    assert extract_education_level(t2) == "Bachelor's Degree"
    print("[PASS] test_v3_experience_and_education passed")


def test_v3_cohort_and_roadmap():
    with open("sample_postings.json", "r", encoding="utf-8") as f:
        postings = json.load(f)

    assert len(postings) == 40, f"Expected 40 postings, got {len(postings)}"
    df = build_skill_frame(postings)
    assert len(df) == 40

    # Cohort comparison: Remote vs Hybrid
    cohort_diff = compare_cohorts(df, "work_model", "Remote", "Hybrid", top_n=10)
    assert not cohort_diff.empty
    assert "diff_a_minus_b" in cohort_diff.columns

    # Salary by skill
    sal_by_skill = calculate_salary_by_skill(df, top_k_skills=8)
    assert not sal_by_skill.empty
    assert "avg_salary" in sal_by_skill.columns

    # Career Roadmap
    user_skills = ["Python", "SQL"]
    roadmap = generate_career_roadmap(df, user_skills, target_domain="Data Science & AI")
    assert "phases" in roadmap
    assert len(roadmap["phases"]) == 4
    print("[PASS] test_v3_cohort_and_roadmap passed")


def test_v3_html_highlighter():
    desc = "We build RAG systems using LangChain, PyTorch, and Docker on AWS."
    html_out = highlight_skills_in_html(desc)
    assert "<mark" in html_out
    assert "PyTorch" in html_out
    assert "LangChain" in html_out
    print("[PASS] test_v3_html_highlighter passed")


if __name__ == "__main__":
    test_v3_salary_extraction()
    test_v3_experience_and_education()
    test_v3_cohort_and_roadmap()
    test_v3_html_highlighter()
    print("\nALL V3 TESTS PASSED SUCCESSFULLY!")
