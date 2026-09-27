"""
Unit and integration test script for Skill Demand Analyzer prototype.
"""

import json
import os
import pandas as pd
from taxonomy import get_default_taxonomy, get_category_for_skill
from extract_analyze import (
    extract_skills,
    deduplicate_postings,
    build_skill_frame,
    skill_frequency,
    skill_cooccurrence,
    filter_postings,
    get_postings_for_skill,
    get_postings_for_pair,
)

def test_extraction_basic():
    text = "Seeking a Data Scientist proficient in Python, SQL, AWS, and Machine learning."
    skills = extract_skills(text)
    assert "Python" in skills, "Python not matched"
    assert "SQL" in skills, "SQL not matched"
    assert "AWS" in skills, "AWS not matched"
    assert "Machine learning" in skills, "Machine learning not matched"
    print("[PASS] test_extraction_basic passed")

def test_extraction_boundaries():
    # Avoid false positives like 'go' in 'algorithms' or 'r' in 'program'
    text = "We want a candidate who can work on algorithms, programming, and cargo."
    skills = extract_skills(text)
    assert "Go" not in skills, "False positive on Go in cargo/algorithms"
    assert "R" not in skills, "False positive on R in programming"
    print("[PASS] test_extraction_boundaries passed")

def test_extraction_cplusplus():
    text = "Required: C++ and C# developer with CI/CD skills."
    skills = extract_skills(text)
    assert "C++" in skills, "C++ not matched"
    assert "C#" in skills, "C# not matched"
    assert "CI/CD" in skills, "CI/CD not matched"
    print("[PASS] test_extraction_cplusplus passed")

def test_pipeline_on_sample():
    with open("sample_postings.json", "r", encoding="utf-8") as f:
        postings = json.load(f)
    
    assert len(postings) == 12, "Expected 12 sample postings"
    
    # Test deduplication with a duplicate inserted
    postings_with_dup = postings + [postings[0]]
    deduped, dup_count = deduplicate_postings(postings_with_dup)
    assert dup_count == 1, f"Expected 1 duplicate, got {dup_count}"
    assert len(deduped) == 12, f"Expected 12 deduped postings, got {len(deduped)}"

    # Test DataFrame construction
    df = build_skill_frame(deduped)
    assert len(df) == 12
    assert "skills" in df.columns
    
    # Test skill frequency
    freq = skill_frequency(df)
    assert not freq.empty
    assert "skill" in freq.columns
    assert "postings_mentioning" in freq.columns
    assert "pct_of_postings" in freq.columns
    top_skill = freq.iloc[0]["skill"]
    assert top_skill == "Python", f"Expected Python top skill, got {top_skill}"

    # Test co-occurrence
    cooc = skill_cooccurrence(df, top_n=10)
    assert not cooc.empty
    assert "skill_a" in cooc.columns
    assert "skill_b" in cooc.columns
    assert "co_occurrences" in cooc.columns

    # Test drill-down
    python_postings = get_postings_for_skill(df, "Python")
    assert len(python_postings) == 10, f"Expected 10 Python postings, got {len(python_postings)}"

    pair_postings = get_postings_for_pair(df, "Python", "SQL")
    assert len(pair_postings) >= 3, f"Expected at least 3 Python+SQL postings, got {len(pair_postings)}"

    print("[PASS] test_pipeline_on_sample passed")

def test_tagged_skills_pipeline():
    with open("data/sample_with_tags.json", "r", encoding="utf-8") as f:
        tagged_postings = json.load(f)

    df_auto = build_skill_frame(tagged_postings, skill_source_mode="auto")
    assert (df_auto["skill_origin"] == "Source Tags").all()
    assert "Snowflake" in df_auto.iloc[0]["skills"]

    df_extract = build_skill_frame(tagged_postings, skill_source_mode="extracted_only")
    assert (df_extract["skill_origin"] == "Extracted from Description").all()

    print("[PASS] test_tagged_skills_pipeline passed")

if __name__ == "__main__":
    test_extraction_basic()
    test_extraction_boundaries()
    test_extraction_cplusplus()
    test_pipeline_on_sample()
    test_tagged_skills_pipeline()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
