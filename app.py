"""
Job Market Skill Demand Analyzer - v2.0 (Production-Grade Prototype)

A comprehensive data analysis application for tech job postings.
Features deterministic regex extraction, multi-dimensional role/seniority inference,
co-occurrence analysis, candidate skill gap matching, interactive text highlighting,
and customizable taxonomy management.
"""

import os
import json
import io
import copy
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import pandas as pd
import altair as alt

from taxonomy import (
    DEFAULT_SKILL_SYNONYMS,
    SKILL_CATEGORIES,
    TAXONOMY_PRESETS,
    get_default_taxonomy,
    get_category_for_skill,
    get_all_categories,
)
from extract_analyze import (
    build_skill_frame,
    deduplicate_postings,
    skill_frequency,
    skill_cooccurrence,
    role_skill_cross_tab,
    seniority_skill_cross_tab,
    calculate_skill_gap,
    filter_postings,
    get_postings_for_skill,
    get_postings_for_pair,
    highlight_skills_in_html,
    compile_taxonomy,
)

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Skill Demand Analyzer v2",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern design aesthetics
st.markdown("""
<style>
    /* Global polish */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E293B, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.0rem;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.80rem;
        color: #475569;
        margin-top: 4px;
    }
    .banner-demo {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #92400E;
        margin-bottom: 1.2rem;
    }
    .banner-user {
        background-color: #ECFDF5;
        border-left: 4px solid #10B981;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #065F46;
        margin-bottom: 1.2rem;
    }
    .badge-chip {
        display: inline-block;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        margin: 2px 4px 2px 0;
    }
    .badge-domain { background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-seniority { background-color: #FAF5FF; color: #7E22CE; border: 1px solid #E9D5FF; }
    .badge-work { background-color: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
    .badge-req { background-color: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
    .badge-pref { background-color: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
    .gap-metric-box {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "taxonomy" not in st.session_state:
    st.session_state.taxonomy = get_default_taxonomy()

if "data_source_mode" not in st.session_state:
    st.session_state.data_source_mode = "demo"

if "raw_postings" not in st.session_state:
    st.session_state.raw_postings = []

if "data_source_label" not in st.session_state:
    st.session_state.data_source_label = "sample_postings.json (25 Illustrative Demo Records)"

if "is_demo" not in st.session_state:
    st.session_state.is_demo = True


# -----------------------------------------------------------------------------
# Data Loading Helpers
# -----------------------------------------------------------------------------
@st.cache_data
def load_bundled_demo_data() -> List[Dict[str, Any]]:
    """Load default sample postings bundled with the project."""
    paths = [
        "sample_postings.json",
        os.path.join("data", "sample_postings.json"),
        os.path.join("zip", "sample_postings.json"),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


def parse_uploaded_file(uploaded_file) -> Tuple[List[Dict[str, Any]], str]:
    """Parse uploaded file (CSV, JSON, TSV, XLSX) into list of dictionaries."""
    try:
        fname = uploaded_file.name
        content = uploaded_file.getvalue()

        if fname.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                return data, fname
            elif isinstance(data, dict):
                for k in ["result", "data", "postings", "jobs"]:
                    if k in data and isinstance(data[k], list):
                        return data[k], fname
                return [data], fname
        elif fname.lower().endswith((".csv", ".tsv", ".txt")):
            delimiter = "\t" if fname.lower().endswith(".tsv") else ","
            df = pd.read_csv(io.StringIO(content.decode("utf-8")), sep=delimiter)
            df = df.fillna("")
            return df.to_dict(orient="records"), fname
        elif fname.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
            df = df.fillna("")
            return df.to_dict(orient="records"), fname
        else:
            raise ValueError("Unsupported file format. Please upload a .json, .csv, .tsv, or .xlsx file.")
    except Exception as exc:
        st.error(f"Failed to read '{uploaded_file.name}': {exc}")
        return [], ""


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/briefcase.png", width=50)
    st.title("Settings & Ingestion")

    st.markdown("### 1. Ingestion Source")
    source_type = st.radio(
        "Choose Input Source:",
        ["🧪 Sample Demo Data", "📁 Upload File (CSV/JSON/XLSX)", "📝 Paste Job Description(s)"],
        index=0 if st.session_state.is_demo else 1,
    )

    if source_type == "🧪 Sample Demo Data":
        st.session_state.is_demo = True
        st.session_state.data_source_label = "sample_postings.json (25 Illustrative Records)"
        st.session_state.raw_postings = load_bundled_demo_data()
        st.info("💡 **Demo Mode:** 25 illustrative tech postings loaded across 7 job domains.")
    
    elif source_type == "📁 Upload File (CSV/JSON/XLSX)":
        st.session_state.is_demo = False
        uploaded_file = st.file_uploader(
            "Upload Job Postings Dataset",
            type=["json", "csv", "tsv", "xlsx"],
            help="Supports standard fields: title, company, description, and optional skills_raw/tags."
        )
        if uploaded_file is not None:
            parsed, fname = parse_uploaded_file(uploaded_file)
            if parsed:
                st.session_state.raw_postings = parsed
                st.session_state.data_source_label = f"Uploaded File: {fname}"
                st.success(f"Loaded {len(parsed)} records from `{fname}`.")
        else:
            st.session_state.raw_postings = []
            st.session_state.data_source_label = "No file loaded"
            st.warning("Please upload a file or switch to Demo Data.")

    elif source_type == "📝 Paste Job Description(s)":
        st.session_state.is_demo = False
        pasted_title = st.text_input("Job Title:", value="Custom Job Posting")
        pasted_company = st.text_input("Company Name:", value="Target Employer")
        pasted_text = st.text_area("Paste Full Job Description:", height=180, placeholder="Paste job description text here...")
        
        if pasted_text.strip():
            st.session_state.raw_postings = [{
                "title": pasted_title,
                "company": pasted_company,
                "posted_at": "Today",
                "description": pasted_text.strip(),
            }]
            st.session_state.data_source_label = "Pasted Job Description"
        else:
            st.session_state.raw_postings = []
            st.session_state.data_source_label = "Empty paste buffer"

    st.markdown("---")

    # Ingestion & Skill Mode Settings
    st.markdown("### 2. Extraction & Taxonomy")
    selected_preset = st.selectbox(
        "Taxonomy Preset:",
        list(TAXONOMY_PRESETS.keys()),
        index=0,
        help="Select a specialized vocabulary preset or manage in the Taxonomy Studio."
    )
    if st.button("Apply Selected Preset"):
        st.session_state.taxonomy = copy.deepcopy(TAXONOMY_PRESETS[selected_preset])
        st.toast(f"Applied preset: {selected_preset}")
        st.rerun()

    skill_handling_mode = st.selectbox(
        "Skill Tag Handling:",
        [
            "Auto (Use tags if present, else extract)",
            "Extracted from Description Only",
            "Source Pre-Tags Only",
            "Combined (Tags + Extracted)",
        ],
        index=0,
    )
    mode_lookup = {
        "Auto (Use tags if present, else extract)": "auto",
        "Extracted from Description Only": "extracted_only",
        "Source Pre-Tags Only": "source_tags_only",
        "Combined (Tags + Extracted)": "combined",
    }
    active_mode = mode_lookup[skill_handling_mode]

    dedup_active = st.checkbox("Deduplicate Postings", value=True, help="Removes duplicate postings with identical title, company, and description.")

    st.markdown("---")
    st.caption(
        "**Job Market Skill Demand Analyzer v2.0**\n\n"
        "• Deterministic regex-based taxonomy engine.\n"
        "• Non-ML data analysis & candidate profiling.\n"
        "• 120+ Curated skills across 8 domains."
    )


# -----------------------------------------------------------------------------
# Main Header & Honesty Status
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">Job Market Skill Demand Analyzer (v2.0)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Multi-dimensional skill demand analysis, role matrix, co-occurrence clustering, and candidate gap evaluation.</div>', unsafe_allow_html=True)

# Honesty Banner
if st.session_state.is_demo:
    st.markdown(
        """
        <div class="banner-demo">
            <strong>🧪 DEMO DATASET ACTIVE:</strong> The insights below are computed from <code>sample_postings.json</code> (25 illustrative records).
            <strong>Demo results are for testing and workflow demonstration only; they do not represent macroeconomic job market statistics.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="banner-user">
            <strong>📁 USER DATASET:</strong> Currently analyzing <code>{st.session_state.data_source_label}</code>.
            Skills, role domains, and seniorities are extracted deterministically based on your active taxonomy configuration.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Validate data
raw_records = st.session_state.raw_postings
if not raw_records:
    st.warning("👈 No postings currently loaded. Please select **Sample Demo Data** or upload a dataset in the sidebar.")
    st.stop()

# Preprocessing & Deduplication
raw_total = len(raw_records)
if dedup_active:
    deduped_records, dups_removed = deduplicate_postings(raw_records)
else:
    deduped_records = raw_records
    dups_removed = 0

# Build Enriched DataFrame
df_all = build_skill_frame(
    deduped_records,
    taxonomy_dict=st.session_state.taxonomy,
    skill_source_mode=active_mode,
)

compiled_tax = compile_taxonomy(st.session_state.taxonomy)


# -----------------------------------------------------------------------------
# Global Multi-Dimensional Filter Bar
# -----------------------------------------------------------------------------
with st.expander("🔍 **Global Filters** (Domain, Seniority, Work Model, Title, Keyword)", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    all_domains = sorted(list(df_all["role_domain"].unique()))
    all_seniorities = sorted(list(df_all["seniority"].unique()))
    all_work_models = sorted(list(df_all["work_model"].unique()))
    all_titles = sorted(list(df_all["title"].unique()))

    with col_f1:
        sel_domains = st.multiselect("Role Domain:", options=all_domains, default=[], placeholder="All Domains")
    with col_f2:
        sel_seniorities = st.multiselect("Seniority Level:", options=all_seniorities, default=[], placeholder="All Seniorities")
    with col_f3:
        sel_work_models = st.multiselect("Work Model:", options=all_work_models, default=[], placeholder="All Models")
    with col_f4:
        kw_query = st.text_input("Keyword Search:", placeholder="e.g., Python, AWS, Docker...")

# Apply Filters
df_filtered = filter_postings(
    df_all,
    selected_domains=sel_domains if sel_domains else None,
    selected_seniorities=sel_seniorities if sel_seniorities else None,
    selected_work_models=sel_work_models if sel_work_models else None,
    keyword=kw_query if kw_query else None,
)

filtered_count = len(df_filtered)
df_freq = skill_frequency(df_filtered)
df_cooc = skill_cooccurrence(df_filtered, top_n=15, min_cooc=1)


# -----------------------------------------------------------------------------
# Summary Key Performance Metrics
# -----------------------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Postings Analyzed</div>
            <div class="metric-value">{filtered_count}</div>
            <div class="metric-sub">{raw_total} raw ({dups_removed} dupes removed)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Unique Skills</div>
            <div class="metric-value">{len(df_freq)}</div>
            <div class="metric-sub">Matched from active taxonomy</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    top_skill = df_freq.iloc[0]["skill"] if not df_freq.empty else "N/A"
    top_pct = f"{df_freq.iloc[0]['pct_of_postings']}%" if not df_freq.empty else "0%"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Top Demanded Skill</div>
            <div class="metric-value">{top_skill}</div>
            <div class="metric-sub">In {top_pct} of filtered postings</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    avg_sk = round(df_filtered["skill_count"].mean(), 1) if not df_filtered.empty else 0.0
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Avg Skills / Job</div>
            <div class="metric-value">{avg_sk}</div>
            <div class="metric-sub">Skills required per posting</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi5:
    top_domain = df_filtered["role_domain"].mode()[0] if not df_filtered.empty else "N/A"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Leading Role Domain</div>
            <div class="metric-value" style="font-size: 1.3rem;">{top_domain}</div>
            <div class="metric-sub">Most frequent job category</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main Tabs Navigation
# -----------------------------------------------------------------------------
tab_overview, tab_matrix, tab_cooc, tab_gap, tab_inspector, tab_tax_studio, tab_report = st.tabs([
    "📊 Skill Demand Overview",
    "🏢 Role & Seniority Matrix",
    "🔗 Co-occurrence & Stack Clusters",
    "🎯 Candidate Skill Gap & Matcher",
    "🔍 Postings Inspector (Drill-Down)",
    "⚙️ Taxonomy Studio",
    "📄 Executive Report",
])


# -----------------------------------------------------------------------------
# TAB 1: Skill Demand Overview
# -----------------------------------------------------------------------------
with tab_overview:
    if df_filtered.empty:
        st.info("No postings match the current filter selection.")
    else:
        col_c1, col_c2 = st.columns([1.3, 1.0])

        with col_c1:
            st.markdown("### 📈 Top Demanded Skills")
            max_limit = min(35, max(5, len(df_freq)))
            top_n_slider = st.slider("Number of skills to chart:", min_value=5, max_value=max_limit, value=min(15, max_limit))

            top_chart_df = df_freq.head(top_n_slider).copy()

            if not top_chart_df.empty:
                chart = (
                    alt.Chart(top_chart_df)
                    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                    .encode(
                        x=alt.X("pct_of_postings:Q", title="% of Job Postings", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("skill:N", sort="-x", title="Canonical Skill"),
                        color=alt.Color("category:N", title="Category", scale=alt.Scale(scheme="tableau10")),
                        tooltip=[
                            alt.Tooltip("skill:N", title="Skill"),
                            alt.Tooltip("category:N", title="Category"),
                            alt.Tooltip("postings_mentioning:Q", title="Postings"),
                            alt.Tooltip("pct_of_postings:Q", title="% of Total"),
                        ],
                    )
                    .properties(height=max(340, top_n_slider * 22))
                    .configure_axis(grid=True, gridDash=[2, 2], gridColor="#E2E8F0")
                )
                st.altair_chart(chart, use_container_width=True)

        with col_c2:
            st.markdown("### 📋 Ranked Skill Demand Table")
            cats = ["All Categories"] + sorted(list(df_freq["category"].unique()))
            chosen_cat = st.selectbox("Filter table by category:", cats)

            filtered_table = df_freq.copy()
            if chosen_cat != "All Categories":
                filtered_table = filtered_table[filtered_table["category"] == chosen_cat]

            st.dataframe(
                filtered_table[[
                    "rank", "skill", "category", "postings_mentioning", "pct_of_postings"
                ]].rename(columns={
                    "rank": "Rank",
                    "skill": "Skill",
                    "category": "Category",
                    "postings_mentioning": "Postings",
                    "pct_of_postings": "% of Postings",
                }),
                use_container_width=True,
                hide_index=True,
                height=380,
            )

            # Download CSV
            csv_blob = filtered_table.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Skill Frequencies (CSV)",
                data=csv_blob,
                file_name=f"skill_frequency_{'demo' if st.session_state.is_demo else 'uploaded'}.csv",
                mime="text/csv",
            )


# -----------------------------------------------------------------------------
# TAB 2: Role & Seniority Matrix
# -----------------------------------------------------------------------------
with tab_matrix:
    st.markdown("### 🏢 Role Domain & Seniority Cross-Tabulation")
    st.markdown(
        "Analyze how skill demand changes across **Role Domains** (e.g. *Data Science* vs *Backend*) "
        "and **Seniority Levels** (e.g. *Junior* vs *Senior/Lead*)."
    )

    mcol1, mcol2 = st.columns(2)

    with mcol1:
        st.markdown("#### 1. Skill Demand by Role Domain")
        role_matrix = role_skill_cross_tab(df_filtered, top_k_skills=8)
        if not role_matrix.empty:
            st.dataframe(role_matrix, use_container_width=True, height=280)
            
            # Melt for heatmap visualization
            melted_role = role_matrix.reset_index().melt(id_vars="role_domain", var_name="skill", value_name="postings_count")
            heat_role = (
                alt.Chart(melted_role)
                .mark_rect()
                .encode(
                    x=alt.X("skill:N", title="Skill"),
                    y=alt.Y("role_domain:N", title="Role Domain"),
                    color=alt.Color("postings_count:Q", title="Postings", scale=alt.Scale(scheme="blues")),
                    tooltip=["role_domain", "skill", "postings_count"],
                )
                .properties(height=240)
            )
            st.altair_chart(heat_role, use_container_width=True)
        else:
            st.info("Insufficient data to build role matrix.")

    with mcol2:
        st.markdown("#### 2. Skill Demand by Seniority Level")
        sen_matrix = seniority_skill_cross_tab(df_filtered, top_k_skills=8)
        if not sen_matrix.empty:
            st.dataframe(sen_matrix, use_container_width=True, height=280)

            melted_sen = sen_matrix.reset_index().melt(id_vars="seniority", var_name="skill", value_name="postings_count")
            heat_sen = (
                alt.Chart(melted_sen)
                .mark_rect()
                .encode(
                    x=alt.X("skill:N", title="Skill"),
                    y=alt.Y("seniority:N", title="Seniority Level"),
                    color=alt.Color("postings_count:Q", title="Postings", scale=alt.Scale(scheme="purples")),
                    tooltip=["seniority", "skill", "postings_count"],
                )
                .properties(height=240)
            )
            st.altair_chart(heat_sen, use_container_width=True)
        else:
            st.info("Insufficient data to build seniority matrix.")


# -----------------------------------------------------------------------------
# TAB 3: Co-occurrence & Stack Clusters
# -----------------------------------------------------------------------------
with tab_cooc:
    st.markdown("### 🔗 Skill Co-occurrence & Tech Stack Combinations")
    MIN_POSTINGS_COOC = 3

    if filtered_count < MIN_POSTINGS_COOC:
        st.info(
            f"ℹ️ Co-occurrence clustering requires at least **{MIN_POSTINGS_COOC} postings** (currently {filtered_count}). "
            "Please broaden your filters or load a larger dataset."
        )
    elif df_cooc.empty:
        st.warning("No co-occurring skill pairs were identified within the current filter selection.")
    else:
        st.markdown(
            "Identifies which skills are most frequently requested together in the same job requirement, "
            "along with **Jaccard Correlation Similarity** (0.0 = never together, 1.0 = always together)."
        )

        ccol1, ccol2 = st.columns([1.2, 1.0])

        with ccol1:
            st.markdown("#### Top Co-occurring Skill Combinations")
            top_cooc_df = df_cooc.head(12).copy()
            top_cooc_df["pair_title"] = top_cooc_df["skill_a"] + " + " + top_cooc_df["skill_b"]

            chart_pairs = (
                alt.Chart(top_cooc_df)
                .mark_bar(color="#4F46E5", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X("co_occurrences:Q", title="Shared Job Postings"),
                    y=alt.Y("pair_title:N", sort="-x", title="Skill Pair"),
                    tooltip=[
                        alt.Tooltip("pair_title:N", title="Skill Combination"),
                        alt.Tooltip("co_occurrences:Q", title="Shared Postings"),
                        alt.Tooltip("pct_of_postings:Q", title="% of Total Jobs"),
                        alt.Tooltip("jaccard_similarity:Q", title="Jaccard Similarity"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(chart_pairs, use_container_width=True)

        with ccol2:
            st.markdown("#### Co-occurrence Matrix")
            st.dataframe(
                df_cooc[[
                    "skill_a", "skill_b", "co_occurrences", "pct_of_postings", "jaccard_similarity"
                ]].rename(columns={
                    "skill_a": "Skill 1",
                    "skill_b": "Skill 2",
                    "co_occurrences": "Shared Jobs",
                    "pct_of_postings": "% of Jobs",
                    "jaccard_similarity": "Jaccard Sim",
                }),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

            cooc_csv_data = df_cooc.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Co-occurrence CSV",
                data=cooc_csv_data,
                file_name="skill_cooccurrence.csv",
                mime="text/csv",
            )


# -----------------------------------------------------------------------------
# TAB 4: Candidate Skill Gap & Matcher
# -----------------------------------------------------------------------------
with tab_gap:
    st.markdown("### 🎯 Candidate Profile & Skill Gap Matcher")
    st.markdown(
        "Enter your current technical skills (or your team's current stack) to calculate **Job Market Match Rate** "
        "and discover the **Highest-ROI Missing Skills** to learn next."
    )

    all_known_skills = sorted(list(st.session_state.taxonomy.keys()))
    default_profile = ["Python", "SQL", "Git"]

    user_selected_skills = st.multiselect(
        "Select your current skills from taxonomy:",
        options=all_known_skills,
        default=[s for s in default_profile if s in all_known_skills],
    )

    if user_selected_skills:
        gap_results = calculate_skill_gap(df_filtered, user_selected_skills)

        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            st.markdown(
                f"""
                <div class="gap-metric-box">
                    <div class="metric-label">Skills in Profile</div>
                    <div class="metric-value">{len(user_selected_skills)}</div>
                    <div class="metric-sub">Active candidate competencies</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with gcol2:
            st.markdown(
                f"""
                <div class="gap-metric-box">
                    <div class="metric-label">50%+ Match Coverage</div>
                    <div class="metric-value" style="color: #2563EB;">{gap_results['match_rate_50pct']}%</div>
                    <div class="metric-sub">You meet &ge;50% of posting requirements</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with gcol3:
            st.markdown(
                f"""
                <div class="gap-metric-box">
                    <div class="metric-label">80%+ Strong Match</div>
                    <div class="metric-value" style="color: #059669;">{gap_results['match_rate_80pct']}%</div>
                    <div class="metric-sub">You meet &ge;80% of posting requirements</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🚀 Highest-Impact Missing Skills to Learn")
        st.markdown("Adding these skills to your profile unlocks the largest number of additional job opportunities:")

        missing_df = pd.DataFrame(gap_results["missing_skills_ranked"])
        if not missing_df.empty:
            m_chart = (
                alt.Chart(missing_df.head(8))
                .mark_bar(color="#059669", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X("pct_unlockable:Q", title="% of Jobs Requiring This Missing Skill"),
                    y=alt.Y("skill:N", sort="-x", title="Recommended Skill to Learn"),
                    color=alt.Color("category:N", title="Category"),
                    tooltip=[
                        alt.Tooltip("skill:N", title="Skill"),
                        alt.Tooltip("category:N", title="Category"),
                        alt.Tooltip("job_mentions:Q", title="Postings Requiring It"),
                        alt.Tooltip("pct_unlockable:Q", title="% of Total Jobs"),
                    ],
                )
                .properties(height=260)
            )
            st.altair_chart(m_chart, use_container_width=True)
        else:
            st.success("🎉 Outstanding! Your skill profile covers all skills identified in the current filter!")


# -----------------------------------------------------------------------------
# TAB 5: Postings Inspector (Drill-Down with HTML Highlighting)
# -----------------------------------------------------------------------------
with tab_inspector:
    st.markdown("### 🔍 Interactive Postings Inspector")
    st.markdown(
        "Drill down into individual job postings with **in-line colored skill highlighting**, "
        "seniority inference, role classification, and required vs preferred skill tags."
    )

    dcol1, dcol2, dcol3 = st.columns([1.2, 1.2, 1.2])

    avail_skills = sorted(list(df_freq["skill"].unique())) if not df_freq.empty else []

    with dcol1:
        inspect_skill = st.selectbox(
            "Primary Skill:",
            options=["(All Skills)"] + avail_skills,
            index=1 if len(avail_skills) > 0 else 0,
        )

    with dcol2:
        secondary_inspect = st.selectbox(
            "Combine with Second Skill (AND):",
            options=["(None)"] + avail_skills,
            index=0,
        )

    with dcol3:
        inspect_domain = st.selectbox(
            "Filter by Domain:",
            options=["(All Domains)"] + sorted(list(df_all["role_domain"].unique())),
            index=0,
        )

    # Filter matching postings
    matching_df = df_filtered.copy()
    if inspect_skill != "(All Skills)":
        if secondary_inspect != "(None)":
            matching_df = get_postings_for_pair(matching_df, inspect_skill, secondary_inspect)
            summary_label = f"postings mentioning both **'{inspect_skill}'** and **'{secondary_inspect}'**"
        else:
            matching_df = get_postings_for_skill(matching_df, inspect_skill)
            summary_label = f"postings mentioning **'{inspect_skill}'**"
    else:
        summary_label = "total postings in current selection"

    if inspect_domain != "(All Domains)":
        matching_df = matching_df[matching_df["role_domain"] == inspect_domain]

    st.markdown(f"Found **{len(matching_df)}** {summary_label}:")

    if matching_df.empty:
        st.info("No postings matched this combination.")
    else:
        for _, row in matching_df.iterrows():
            with st.container():
                st.markdown(f"#### 📌 {row['title']} — *{row['company']}*")

                # Provenance & Metadata Chips
                badges_html = [
                    f"<span class='badge-chip badge-domain'>📂 {row['role_domain']}</span>",
                    f"<span class='badge-chip badge-seniority'>🎖️ {row['seniority']}</span>",
                    f"<span class='badge-chip badge-work'>📍 {row['work_model']} ({row['country']})</span>",
                    f"<span class='badge-chip'>📅 {row['posted_at']}</span>",
                    f"<span class='badge-chip'>🏷️ Origin: {row['skill_origin']}</span>",
                ]
                st.markdown("".join(badges_html), unsafe_allow_html=True)

                # Skill Chips
                skills_present = row["skills"]
                if skills_present:
                    chips_html = "".join([f"<span class='badge-chip badge-req'>{s}</span>" for s in skills_present])
                    st.markdown(f"**Identified Skills ({len(skills_present)}):**<br>{chips_html}", unsafe_allow_html=True)

                # Highlighted Job Description Expander
                with st.expander("📄 View Full Job Description (with In-Line Skill Highlights)", expanded=False):
                    highlighted_html = highlight_skills_in_html(row["description"], compiled_tax)
                    st.markdown(highlighted_html, unsafe_allow_html=True)

                st.markdown("---")

        # Export JSON of inspected postings
        inspected_json = matching_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            "📥 Download Filtered Postings (JSON)",
            data=inspected_json,
            file_name="inspected_postings.json",
            mime="application/json",
        )


# -----------------------------------------------------------------------------
# TAB 6: Taxonomy Studio
# -----------------------------------------------------------------------------
with tab_tax_studio:
    st.markdown("### ⚙️ Skills Taxonomy Studio")
    st.markdown(
        "Manage, customize, export, and import the skills dictionary used for keyword and regex matching."
    )

    t1, t2 = st.columns([1.1, 1.1])

    with t1:
        st.markdown("#### ➕ Add or Update a Skill")
        with st.form("custom_skill_form"):
            new_canonical = st.text_input("Canonical Skill Name:", placeholder="e.g. Polars, LangGraph, Terraform")
            new_syns = st.text_area(
                "Aliases / Surface Forms (comma-separated):",
                placeholder="e.g. polars, python polars, polars-dataframe",
            )
            submit_skill_btn = st.form_submit_button("Save Skill to Taxonomy")

            if submit_skill_btn:
                if new_canonical.strip() and new_syns.strip():
                    aliases = [a.strip() for a in new_syns.split(",") if a.strip()]
                    st.session_state.taxonomy[new_canonical.strip()] = aliases
                    st.success(f"Added '{new_canonical.strip()}' with {len(aliases)} synonyms!")
                    st.rerun()
                else:
                    st.error("Please provide both a canonical name and at least one synonym alias.")

        st.markdown("#### 🔄 Reset to Default Taxonomy")
        if st.button("Reset Taxonomy to Default (120+ Skills)"):
            st.session_state.taxonomy = get_default_taxonomy()
            st.success("Taxonomy reset to default configuration.")
            st.rerun()

    with t2:
        st.markdown("#### 💾 Export & Import Taxonomy")
        tax_json_str = json.dumps(st.session_state.taxonomy, indent=2)
        st.download_button(
            "📥 Export Taxonomy as JSON",
            data=tax_json_str.encode("utf-8"),
            file_name="skills_taxonomy.json",
            mime="application/json",
            help="Download the active taxonomy JSON to share with teammates."
        )

        uploaded_tax = st.file_uploader("Upload Custom Taxonomy JSON:", type=["json"], key="tax_upload")
        if uploaded_tax is not None:
            try:
                custom_tax = json.loads(uploaded_tax.getvalue().decode("utf-8"))
                if isinstance(custom_tax, dict):
                    st.session_state.taxonomy = custom_tax
                    st.success(f"Successfully loaded custom taxonomy with {len(custom_tax)} skills!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing taxonomy file: {e}")

    st.markdown("---")
    st.markdown("#### Current Active Taxonomy Dictionary")
    tax_table_rows = []
    for sk, syns in sorted(st.session_state.taxonomy.items()):
        tax_table_rows.append({
            "Canonical Skill": sk,
            "Category": get_category_for_skill(sk),
            "Synonyms Count": len(syns),
            "Aliases": ", ".join(syns),
        })
    df_tax_display = pd.DataFrame(tax_table_rows)
    st.dataframe(df_tax_display, use_container_width=True, height=320, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 7: Executive Report Generator
# -----------------------------------------------------------------------------
with tab_report:
    st.markdown("### 📄 Executive Summary Report")
    st.markdown("A ready-to-share summary of key findings generated from the active dataset and filter selection.")

    top_3_skills = df_freq.head(3)["skill"].tolist() if not df_freq.empty else ["N/A"]
    top_3_str = ", ".join(top_3_skills)
    top_cooc_str = f"{df_cooc.iloc[0]['skill_a']} + {df_cooc.iloc[0]['skill_b']}" if not df_cooc.empty else "N/A"

    report_md = f"""# Executive Job Market Skill Demand Summary
**Dataset Source:** {st.session_state.data_source_label}  
**Total Postings Analyzed:** {filtered_count} (out of {raw_total} raw records, {dups_removed} duplicates removed)  
**Analysis Engine:** Skill Demand Analyzer v2.0 (Deterministic Taxonomy Engine)  

---

## 🔑 Key Takeaways & Highlights

1. **Top Demanded Competencies:**
   - The top 3 most requested skills are **{top_3_str}**.
   - Leading skill **{top_skill}** appears in **{top_pct}** of all analyzed postings.

2. **Dominant Technical Domain:**
   - **{top_domain}** represents the largest job concentration in this dataset.

3. **Prominent Tech Stack Pairings:**
   - The most frequent co-occurring skill combination is **{top_cooc_str}**.

4. **Skill Diversity:**
   - An average of **{avg_sk} skills** are explicitly requested per job posting.

---

## 📊 Top 10 Ranked Skills

| Rank | Skill | Category | Postings Mentioning | % of Postings |
| :---: | :--- | :--- | :---: | :---: |
"""
    for _, r in df_freq.head(10).iterrows():
        report_md += f"| {r['rank']} | {r['skill']} | {r['category']} | {r['postings_mentioning']} | {r['pct_of_postings']}% |\n"

    report_md += f"""
---
*Disclaimer: This report was generated deterministically by matching job posting text against a curated skills taxonomy. Sample demo datasets reflect internal prototype distributions and do not represent empirical macroeconomic job market statistics.*
"""

    st.markdown(report_md)

    st.download_button(
        "📥 Download Executive Summary (Markdown)",
        data=report_md.encode("utf-8"),
        file_name="executive_skill_report.md",
        mime="text/markdown",
    )
