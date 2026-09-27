"""
Job Market Skill Demand Analyzer - v3.0 (Enterprise Data Intelligence Edition)

Features:
- Multi-dimensional skill extraction & weighted demand scoring (180+ taxonomy)
- Salary & compensation analytics with top-paying skill leaderboards
- Role domain, seniority level, years of experience, & degree requirements matrix
- A/B Cohort Comparison Studio (e.g. Remote vs Onsite, Senior vs Junior)
- 4-Phase Career Learning Roadmap generator
- Co-occurrence clustering with Jaccard correlation
- In-line HTML skill highlighter with tooltips
- Complete export suite & executive summary report generator
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
    calculate_salary_by_skill,
    compare_cohorts,
    generate_career_roadmap,
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
    page_title="Skill Demand Analyzer v3.0",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern Custom CSS styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0F172A, #2563EB, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 1.02rem;
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
        box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 1.7rem;
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
    .badge-salary { background-color: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-weight:700; }
    .badge-exp { background-color: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
    .badge-work { background-color: #F8FAFC; color: #334155; border: 1px solid #CBD5E1; }
    .badge-req { background-color: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
    .roadmap-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
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
    st.session_state.data_source_label = "sample_postings.json (40 Comprehensive Demo Records)"

if "is_demo" not in st.session_state:
    st.session_state.is_demo = True


# -----------------------------------------------------------------------------
# Data Loading Helpers
# -----------------------------------------------------------------------------
@st.cache_data
def load_bundled_demo_data() -> List[Dict[str, Any]]:
    """Load default 40-posting sample dataset bundled with project."""
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
    """Parse uploaded file into list of dictionaries."""
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
            delim = "\t" if fname.lower().endswith(".tsv") else ","
            df = pd.read_csv(io.StringIO(content.decode("utf-8")), sep=delim)
            df = df.fillna("")
            return df.to_dict(orient="records"), fname
        elif fname.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
            df = df.fillna("")
            return df.to_dict(orient="records"), fname
        else:
            raise ValueError("Unsupported format. Please upload a .json, .csv, .tsv, or .xlsx file.")
    except Exception as exc:
        st.error(f"Failed to read '{uploaded_file.name}': {exc}")
        return [], ""


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/briefcase.png", width=48)
    st.title("Settings & Ingestion")

    st.markdown("### 1. Ingestion Source")
    source_type = st.radio(
        "Choose Input Source:",
        ["🧪 Sample Demo Data (40 Postings)", "📁 Upload File (CSV/JSON/XLSX)", "📝 Paste Job Description(s)"],
        index=0 if st.session_state.is_demo else 1,
    )

    if source_type == "🧪 Sample Demo Data (40 Postings)":
        st.session_state.is_demo = True
        st.session_state.data_source_label = "sample_postings.json (40 Comprehensive Records)"
        st.session_state.raw_postings = load_bundled_demo_data()
        st.info("💡 **Demo Active:** 40 postings loaded with salaries, experience requirements, and degrees.")

    elif source_type == "📁 Upload File (CSV/JSON/XLSX)":
        st.session_state.is_demo = False
        uploaded_file = st.file_uploader(
            "Upload Job Postings Dataset",
            type=["json", "csv", "tsv", "xlsx"],
            help="Supports standard fields: title, company, description, salary, skills_raw/tags."
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
        pasted_title = st.text_input("Job Title:", value="Senior AI / ML Engineer")
        pasted_company = st.text_input("Company Name:", value="Target Employer")
        pasted_sal = st.text_input("Salary (Optional):", value="$150,000 - $200,000 / year")
        pasted_text = st.text_area("Paste Full Job Description:", height=160, placeholder="Paste job description text here...")

        if pasted_text.strip():
            st.session_state.raw_postings = [{
                "title": pasted_title,
                "company": pasted_company,
                "salary": pasted_sal,
                "posted_at": "Today",
                "description": pasted_text.strip(),
            }]
            st.session_state.data_source_label = "Pasted Job Description"
        else:
            st.session_state.raw_postings = []
            st.session_state.data_source_label = "Empty paste buffer"

    st.markdown("---")

    # Ingestion & Skill Mode Settings
    st.markdown("### 2. Taxonomy & Sourcing")
    selected_preset = st.selectbox(
        "Taxonomy Preset:",
        list(TAXONOMY_PRESETS.keys()),
        index=0,
    )
    if st.button("Apply Selected Preset"):
        st.session_state.taxonomy = copy.deepcopy(TAXONOMY_PRESETS[selected_preset])
        st.toast(f"Applied preset: {selected_preset}")
        st.rerun()

    skill_handling_mode = st.selectbox(
        "Skill Sourcing Mode:",
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

    dedup_active = st.checkbox("Deduplicate Postings", value=True, help="Removes duplicate postings sharing title, company, and description.")

    st.markdown("---")
    st.caption(
        "**Job Market Skill Demand Analyzer v3.0**\n\n"
        "• 180+ Curated skills across 10 domains.\n"
        "• Salary intelligence & A/B cohort analysis.\n"
        "• Deterministic regex parsing (No ML inference)."
    )


# -----------------------------------------------------------------------------
# Main Header & Honesty Status
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">Job Market Skill Demand Analyzer (v3.0)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced multi-dimensional skill analytics, compensation intelligence, A/B cohort benchmarking, and career roadmaps.</div>', unsafe_allow_html=True)

if st.session_state.is_demo:
    st.markdown(
        """
        <div class="banner-demo">
            <strong>🧪 DEMO DATASET ACTIVE:</strong> The insights below are computed from <code>sample_postings.json</code> (40 illustrative records).
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
            Skills, salaries, role domains, and seniorities are extracted deterministically based on your active taxonomy configuration.
        </div>
        """,
        unsafe_allow_html=True,
    )

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
with st.expander("🔍 **Global Filters** (Domain, Seniority, Work Model, Degree, Keyword)", expanded=True):
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)

    all_domains = sorted(list(df_all["role_domain"].unique()))
    all_seniorities = sorted(list(df_all["seniority"].unique()))
    all_work_models = sorted(list(df_all["work_model"].unique()))
    all_educations = sorted(list(df_all["education_level"].unique()))

    with col_f1:
        sel_domains = st.multiselect("Domain:", options=all_domains, default=[], placeholder="All Domains")
    with col_f2:
        sel_seniorities = st.multiselect("Seniority:", options=all_seniorities, default=[], placeholder="All Seniorities")
    with col_f3:
        sel_work_models = st.multiselect("Work Model:", options=all_work_models, default=[], placeholder="All Models")
    with col_f4:
        sel_educations = st.multiselect("Degree:", options=all_educations, default=[], placeholder="All Degrees")
    with col_f5:
        kw_query = st.text_input("Keyword Search:", placeholder="e.g., Python, AWS, Docker...")

# Apply Filters
df_filtered = filter_postings(
    df_all,
    selected_domains=sel_domains if sel_domains else None,
    selected_seniorities=sel_seniorities if sel_seniorities else None,
    selected_work_models=sel_work_models if sel_work_models else None,
    selected_educations=sel_educations if sel_educations else None,
    keyword=kw_query if kw_query else None,
)

filtered_count = len(df_filtered)
df_freq = skill_frequency(df_filtered)
df_cooc = skill_cooccurrence(df_filtered, top_n=15, min_cooc=1)
df_salary_by_skill = calculate_salary_by_skill(df_filtered, top_k_skills=12)


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
            <div class="metric-sub">Across 10 tech domains</div>
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
    sal_postings = df_filtered[df_filtered["has_salary"]]
    avg_comp_str = f"${int(sal_postings['salary_avg'].mean()):,}" if not sal_postings.empty else "N/A"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Avg Compensation</div>
            <div class="metric-value" style="color: #059669;">{avg_comp_str}</div>
            <div class="metric-sub">From {len(sal_postings)} disclosed salaries</div>
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
            <div class="metric-sub">Largest concentration</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main Tabs Navigation (9 Feature-Packed Tabs)
# -----------------------------------------------------------------------------
(
    tab_demand,
    tab_salary,
    tab_matrix,
    tab_cohort,
    tab_cooc,
    tab_roadmap,
    tab_inspector,
    tab_tax_studio,
    tab_report,
) = st.tabs([
    "📊 Skill Demand & Weighted Priority",
    "💰 Salary & Compensation Analytics",
    "🏢 Role, Seniority & Experience Matrix",
    "⚖️ A/B Cohort Comparison Studio",
    "🔗 Co-occurrence & Stack Clusters",
    "🎯 Career Roadmap & Skill Gap Matcher",
    "🔍 Postings Inspector (Drill-Down)",
    "⚙️ Taxonomy & ESCO Studio",
    "📄 Executive & Export Center",
])


# -----------------------------------------------------------------------------
# TAB 1: Skill Demand & Weighted Priority
# -----------------------------------------------------------------------------
with tab_demand:
    if df_filtered.empty:
        st.info("No postings match the current filter selection.")
    else:
        col_c1, col_c2 = st.columns([1.3, 1.0])

        with col_c1:
            st.markdown("### 📈 Top Demanded Skills")
            metric_view = st.radio(
                "Ranking Metric:",
                ["Market Share (% of Postings)", "Weighted Demand Score (Required > Preferred)"],
                horizontal=True,
            )

            max_limit = min(40, max(5, len(df_freq)))
            top_n_slider = st.slider("Number of skills to chart:", min_value=5, max_value=max_limit, value=min(15, max_limit))
            top_chart_df = df_freq.head(top_n_slider).copy()

            x_field = "pct_of_postings:Q" if "Market Share" in metric_view else "weighted_score:Q"
            x_title = "% of Job Postings" if "Market Share" in metric_view else "Weighted Demand Score"

            chart = (
                alt.Chart(top_chart_df)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X(x_field, title=x_title),
                    y=alt.Y("skill:N", sort="-x", title="Canonical Skill"),
                    color=alt.Color("category:N", title="Category", scale=alt.Scale(scheme="tableau10")),
                    tooltip=[
                        alt.Tooltip("skill:N", title="Skill"),
                        alt.Tooltip("category:N", title="Category"),
                        alt.Tooltip("postings_mentioning:Q", title="Postings Mentioning"),
                        alt.Tooltip("pct_of_postings:Q", title="% of Total"),
                        alt.Tooltip("weighted_score:Q", title="Weighted Score"),
                    ],
                )
                .properties(height=max(360, top_n_slider * 22))
                .configure_axis(grid=True, gridDash=[2, 2], gridColor="#E2E8F0")
            )
            st.altair_chart(chart, use_container_width=True)

        with col_c2:
            st.markdown("### 📋 Ranked Skill Demand Table")
            cats = ["All Categories"] + sorted(list(df_freq["category"].unique()))
            chosen_cat = st.selectbox("Filter table by category:", cats, key="cat_sel_t1")

            filtered_table = df_freq.copy()
            if chosen_cat != "All Categories":
                filtered_table = filtered_table[filtered_table["category"] == chosen_cat]

            st.dataframe(
                filtered_table[[
                    "rank", "skill", "category", "postings_mentioning", "pct_of_postings", "weighted_score"
                ]].rename(columns={
                    "rank": "Rank",
                    "skill": "Skill",
                    "category": "Category",
                    "postings_mentioning": "Postings",
                    "pct_of_postings": "% of Jobs",
                    "weighted_score": "Weighted Score",
                }),
                use_container_width=True,
                hide_index=True,
                height=380,
            )

            csv_blob = filtered_table.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Skill Demand CSV",
                data=csv_blob,
                file_name=f"skill_demand_{'demo' if st.session_state.is_demo else 'uploaded'}.csv",
                mime="text/csv",
            )


# -----------------------------------------------------------------------------
# TAB 2: Salary & Compensation Analytics
# -----------------------------------------------------------------------------
with tab_salary:
    st.markdown("### 💰 Compensation & Salary by Skill")
    st.markdown(
        "Explore average compensation distributions and discover the **Top-Paying Technical Skills** "
        "extracted from job postings with disclosed compensation."
    )

    if df_salary_by_skill.empty:
        st.info("No salary ranges were detected in the currently filtered postings.")
    else:
        scol1, scol2 = st.columns([1.3, 1.0])

        with scol1:
            st.markdown("#### 🏆 Highest-Paying Skills Leaderboard")
            chart_sal = (
                alt.Chart(df_salary_by_skill.head(12))
                .mark_bar(color="#059669", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X("avg_salary:Q", title="Average Annual Compensation ($ USD)", scale=alt.Scale(domain=[50000, 260000])),
                    y=alt.Y("skill:N", sort="-x", title="Skill"),
                    color=alt.Color("category:N", title="Category"),
                    tooltip=[
                        alt.Tooltip("skill:N", title="Skill"),
                        alt.Tooltip("avg_salary:Q", title="Average Salary ($)", format="$,.0f"),
                        alt.Tooltip("min_salary:Q", title="Min Disclosed ($)", format="$,.0f"),
                        alt.Tooltip("max_salary:Q", title="Max Disclosed ($)", format="$,.0f"),
                        alt.Tooltip("postings_with_salary:Q", title="Postings Sample"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(chart_sal, use_container_width=True)

        with scol2:
            st.markdown("#### 💵 Skill Salary Breakdown")
            st.dataframe(
                df_salary_by_skill[[
                    "skill", "category", "avg_salary", "min_salary", "max_salary", "postings_with_salary"
                ]].rename(columns={
                    "skill": "Skill",
                    "category": "Category",
                    "avg_salary": "Avg Salary ($)",
                    "min_salary": "Min ($)",
                    "max_salary": "Max ($)",
                    "postings_with_salary": "Sample Size",
                }),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

            sal_csv = df_salary_by_skill.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Salary Leaderboard (CSV)", data=sal_csv, file_name="salary_by_skill.csv", mime="text/csv")


# -----------------------------------------------------------------------------
# TAB 3: Role, Seniority & Experience Matrix
# -----------------------------------------------------------------------------
with tab_matrix:
    st.markdown("### 🏢 Role Domain, Seniority & Experience Matrix")
    st.markdown("Cross-tabulate skill requirements against **Job Domains**, **Seniority Levels**, and **Years of Experience**.")

    m1, m2 = st.columns(2)

    with m1:
        st.markdown("#### 1. Skill Demand by Role Domain")
        role_matrix = role_skill_cross_tab(df_filtered, top_k_skills=8)
        if not role_matrix.empty:
            melted_role = role_matrix.reset_index().melt(id_vars="role_domain", var_name="skill", value_name="count")
            heat_role = (
                alt.Chart(melted_role)
                .mark_rect()
                .encode(
                    x=alt.X("skill:N", title="Skill"),
                    y=alt.Y("role_domain:N", title="Role Domain"),
                    color=alt.Color("count:Q", title="Postings", scale=alt.Scale(scheme="blues")),
                    tooltip=["role_domain", "skill", "count"],
                )
                .properties(height=260)
            )
            st.altair_chart(heat_role, use_container_width=True)
            st.dataframe(role_matrix, use_container_width=True, height=200)
        else:
            st.info("Insufficient data for role matrix.")

    with m2:
        st.markdown("#### 2. Skill Demand by Seniority Level")
        sen_matrix = seniority_skill_cross_tab(df_filtered, top_k_skills=8)
        if not sen_matrix.empty:
            melted_sen = sen_matrix.reset_index().melt(id_vars="seniority", var_name="skill", value_name="count")
            heat_sen = (
                alt.Chart(melted_sen)
                .mark_rect()
                .encode(
                    x=alt.X("skill:N", title="Skill"),
                    y=alt.Y("seniority:N", title="Seniority"),
                    color=alt.Color("count:Q", title="Postings", scale=alt.Scale(scheme="purples")),
                    tooltip=["seniority", "skill", "count"],
                )
                .properties(height=260)
            )
            st.altair_chart(heat_sen, use_container_width=True)
            st.dataframe(sen_matrix, use_container_width=True, height=200)
        else:
            st.info("Insufficient data for seniority matrix.")


# -----------------------------------------------------------------------------
# TAB 4: A/B Cohort Comparison Studio
# -----------------------------------------------------------------------------
with tab_cohort:
    st.markdown("### ⚖️ A/B Cohort Comparison Studio")
    st.markdown("Compare skill demand differences between two distinct job cohorts side-by-side.")

    c_opt1, c_opt2, c_opt3 = st.columns(3)

    with c_opt1:
        cohort_dim = st.selectbox(
            "Comparison Dimension:",
            ["Work Model (Remote vs Hybrid/Onsite)", "Seniority (Senior vs Junior)", "Domain (Data Science vs Data Eng)"],
        )

    # Resolve values
    if "Work Model" in cohort_dim:
        dim_col = "work_model"
        v_a, v_b = "Remote", "Hybrid"
    elif "Seniority" in cohort_dim:
        dim_col = "seniority"
        v_a, v_b = "Senior / Lead", "Junior / Associate"
    else:
        dim_col = "role_domain"
        v_a, v_b = "Data Science & AI", "Data Engineering"

    with c_opt2:
        cohort_a = st.selectbox("Cohort A:", sorted(list(df_all[dim_col].unique())), index=0)
    with c_opt3:
        cohort_b = st.selectbox("Cohort B:", sorted(list(df_all[dim_col].unique())), index=min(1, len(df_all[dim_col].unique()) - 1))

    cohort_diff_df = compare_cohorts(df_all, dim_col, cohort_a, cohort_b, top_n=12)

    if cohort_diff_df.empty:
        st.warning("One or both cohorts do not have enough postings to perform comparative analysis.")
    else:
        comp1, comp2 = st.columns([1.3, 1.0])

        with comp1:
            st.markdown(f"#### 📊 Skill Prevalence: **{cohort_a}** vs **{cohort_b}**")
            
            # Melt for grouped comparison chart
            melted_cohort = cohort_diff_df.melt(
                id_vars=["skill", "category"],
                value_vars=[f"pct_{cohort_a}", f"pct_{cohort_b}"],
                var_name="Cohort",
                value_name="Percentage",
            )
            melted_cohort["Cohort"] = melted_cohort["Cohort"].str.replace("pct_", "")

            chart_cohort = (
                alt.Chart(melted_cohort)
                .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
                .encode(
                    x=alt.X("Percentage:Q", title="% of Postings in Cohort"),
                    y=alt.Y("skill:N", sort="-x", title="Skill"),
                    color=alt.Color("Cohort:N", scale=alt.Scale(range=["#2563EB", "#F59E0B"])),
                    xOffset="Cohort:N",
                    tooltip=["skill", "Cohort", "Percentage"],
                )
                .properties(height=360)
            )
            st.altair_chart(chart_cohort, use_container_width=True)

        with comp2:
            st.markdown(f"#### 📈 Relative Difference (Lift)")
            st.dataframe(
                cohort_diff_df[[
                    "skill", f"pct_{cohort_a}", f"pct_{cohort_b}", "diff_a_minus_b"
                ]].rename(columns={
                    "skill": "Skill",
                    f"pct_{cohort_a}": f"{cohort_a} (%)",
                    f"pct_{cohort_b}": f"{cohort_b} (%)",
                    "diff_a_minus_b": f"Diff ({cohort_a} - {cohort_b})",
                }),
                use_container_width=True,
                hide_index=True,
                height=360,
            )


# -----------------------------------------------------------------------------
# TAB 5: Co-occurrence & Stack Clusters
# -----------------------------------------------------------------------------
with tab_cooc:
    st.markdown("### 🔗 Skill Co-occurrence & Stack Combinations")
    if filtered_count < 3:
        st.info("Co-occurrence analysis requires at least 3 job postings.")
    elif df_cooc.empty:
        st.warning("No co-occurring skill pairs found in current filter.")
    else:
        st.markdown("Discover which skills frequently appear together in the same job requirement with **Jaccard Correlation Similarity**.")

        ccol1, ccol2 = st.columns([1.2, 1.0])

        with ccol1:
            st.markdown("#### Top Co-occurring Pairs")
            top_cooc_df = df_cooc.head(12).copy()
            top_cooc_df["pair_label"] = top_cooc_df["skill_a"] + " + " + top_cooc_df["skill_b"]

            chart_pairs = (
                alt.Chart(top_cooc_df)
                .mark_bar(color="#4F46E5", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X("co_occurrences:Q", title="Shared Postings"),
                    y=alt.Y("pair_label:N", sort="-x", title="Skill Pair"),
                    tooltip=[
                        alt.Tooltip("pair_label:N", title="Combination"),
                        alt.Tooltip("co_occurrences:Q", title="Shared Postings"),
                        alt.Tooltip("pct_of_postings:Q", title="% of Jobs"),
                        alt.Tooltip("jaccard_similarity:Q", title="Jaccard Sim"),
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

            cooc_csv = df_cooc.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Co-occurrence CSV", data=cooc_csv, file_name="skill_cooccurrence.csv", mime="text/csv")


# -----------------------------------------------------------------------------
# TAB 6: Career Roadmap & Candidate Matcher
# -----------------------------------------------------------------------------
with tab_roadmap:
    st.markdown("### 🎯 Career Roadmap & Candidate Skill Matcher")
    st.markdown("Enter your current skillset to calculate **Job Match Coverage** and generate a **Step-by-Step Learning Path** toward your target domain.")

    all_known_skills = sorted(list(st.session_state.taxonomy.keys()))
    default_profile = ["Python", "SQL", "Git"]

    rcol1, rcol2 = st.columns([1.5, 1.0])

    with rcol1:
        user_skills_input = st.multiselect(
            "Select your current skills from taxonomy:",
            options=all_known_skills,
            default=[s for s in default_profile if s in all_known_skills],
            key="user_skills_roadmap",
        )

    with rcol2:
        target_role = st.selectbox(
            "Target Career Domain:",
            ["All Roles"] + sorted(list(df_all["role_domain"].unique())),
        )

    if user_skills_input:
        gap_results = calculate_skill_gap(df_filtered, user_skills_input)
        roadmap_data = generate_career_roadmap(df_filtered, user_skills_input, target_role)

        gcol1, gcol2, gcol3 = st.columns(3)
        with gcol1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Skills in Profile</div>
                    <div class="metric-value">{len(user_skills_input)}</div>
                    <div class="metric-sub">Active competencies</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with gcol2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">50%+ Match Coverage</div>
                    <div class="metric-value" style="color: #2563EB;">{gap_results['match_rate_50pct']}%</div>
                    <div class="metric-sub">Qualified for &ge;50% of requirements</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with gcol3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">80%+ Strong Match</div>
                    <div class="metric-value" style="color: #059669;">{gap_results['match_rate_80pct']}%</div>
                    <div class="metric-sub">Qualified for &ge;80% of requirements</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"#### 🗺️ 4-Phase Learning Roadmap for **{target_role}**")

        for phase_title, phase_skills in roadmap_data["phases"].items():
            with st.container():
                st.markdown(f"##### {phase_title}")
                if phase_skills:
                    chips = "".join([f"<span class='badge-chip badge-req'>{s['skill']} ({s['pct_of_jobs']}% jobs)</span>" for s in phase_skills])
                    st.markdown(f"<div class='roadmap-card'>{chips}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='roadmap-card'><em>✅ You already cover all core skills in this phase!</em></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TAB 7: Postings Inspector (Drill-Down with In-Line Highlighting)
# -----------------------------------------------------------------------------
with tab_inspector:
    st.markdown("### 🔍 Interactive Postings Inspector")
    st.markdown("Drill down into individual job postings with **in-line colored skill highlighting**, salary badges, experience chips, and full descriptions.")

    dcol1, dcol2, dcol3 = st.columns([1.2, 1.2, 1.2])

    avail_skills = sorted(list(df_freq["skill"].unique())) if not df_freq.empty else []

    with dcol1:
        inspect_skill = st.selectbox("Primary Skill:", options=["(All Skills)"] + avail_skills, index=1 if len(avail_skills) > 0 else 0)
    with dcol2:
        secondary_inspect = st.selectbox("Second Skill (AND):", options=["(None)"] + avail_skills, index=0)
    with dcol3:
        inspect_domain = st.selectbox("Domain:", options=["(All Domains)"] + sorted(list(df_all["role_domain"].unique())), index=0)

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
        st.info("No postings match this combination.")
    else:
        for _, row in matching_df.iterrows():
            with st.container():
                st.markdown(f"#### 📌 {row['title']} — *{row['company']}*")

                badges = [
                    f"<span class='badge-chip badge-domain'>📂 {row['role_domain']}</span>",
                    f"<span class='badge-chip badge-seniority'>🎖️ {row['seniority']}</span>",
                    f"<span class='badge-chip badge-work'>📍 {row['work_model']} ({row['country']})</span>",
                ]
                if row["has_salary"] and row["salary_avg"]:
                    badges.append(f"<span class='badge-chip badge-salary'>💵 ~${row['salary_avg']:,}/yr</span>")
                if row["min_years_experience"]:
                    badges.append(f"<span class='badge-chip badge-exp'>⏳ {row['min_years_experience']}+ yrs exp</span>")
                if row["education_level"] != "Not Specified":
                    badges.append(f"<span class='badge-chip'>🎓 {row['education_level']}</span>")

                st.markdown("".join(badges), unsafe_allow_html=True)

                # Skill chips
                skills_present = row["skills"]
                if skills_present:
                    chips_html = "".join([f"<span class='badge-chip badge-req'>{s}</span>" for s in skills_present])
                    st.markdown(f"**Identified Skills ({len(skills_present)}):**<br>{chips_html}", unsafe_allow_html=True)

                with st.expander("📄 View Full Job Description (with In-Line Skill Highlights)", expanded=False):
                    highlighted_html = highlight_skills_in_html(row["description"], compiled_tax)
                    st.markdown(highlighted_html, unsafe_allow_html=True)

                st.markdown("---")

        inspected_json = matching_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button("📥 Download Filtered Postings (JSON)", data=inspected_json, file_name="inspected_postings.json", mime="application/json")


# -----------------------------------------------------------------------------
# TAB 8: Taxonomy & ESCO Studio
# -----------------------------------------------------------------------------
with tab_tax_studio:
    st.markdown("### ⚙️ Taxonomy & ESCO Studio")
    st.markdown("Manage, customize, export, and import the 180+ skill dictionary aligned with standard occupational taxonomies.")

    t1, t2 = st.columns([1.1, 1.1])

    with t1:
        st.markdown("#### ➕ Add or Update a Skill")
        with st.form("custom_skill_form_v3"):
            new_canonical = st.text_input("Canonical Skill Name:", placeholder="e.g. Polars, LangGraph, Terraform")
            new_syns = st.text_area("Aliases / Surface Forms (comma-separated):", placeholder="e.g. polars, python polars, polars-dataframe")
            submit_skill_btn = st.form_submit_button("Save Skill to Taxonomy")

            if submit_skill_btn:
                if new_canonical.strip() and new_syns.strip():
                    aliases = [a.strip() for a in new_syns.split(",") if a.strip()]
                    st.session_state.taxonomy[new_canonical.strip()] = aliases
                    st.success(f"Added '{new_canonical.strip()}' with {len(aliases)} synonyms!")
                    st.rerun()
                else:
                    st.error("Please provide both a canonical name and at least one synonym alias.")

        if st.button("Reset Taxonomy to Default (180+ Skills)"):
            st.session_state.taxonomy = get_default_taxonomy()
            st.success("Taxonomy reset to default configuration.")
            st.rerun()

    with t2:
        st.markdown("#### 💾 Export & Import Taxonomy")
        tax_json_str = json.dumps(st.session_state.taxonomy, indent=2)
        st.download_button("📥 Export Taxonomy as JSON", data=tax_json_str.encode("utf-8"), file_name="skills_taxonomy.json", mime="application/json")

        uploaded_tax = st.file_uploader("Upload Custom Taxonomy JSON:", type=["json"], key="tax_upload_v3")
        if uploaded_tax is not None:
            try:
                custom_tax = json.loads(uploaded_tax.getvalue().decode("utf-8"))
                if isinstance(custom_tax, dict):
                    st.session_state.taxonomy = custom_tax
                    st.success(f"Loaded custom taxonomy with {len(custom_tax)} skills!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing taxonomy file: {e}")

    st.markdown("---")
    st.markdown("#### Active Taxonomy Dictionary (180+ Skills)")
    tax_table_rows = []
    for sk, syns in sorted(st.session_state.taxonomy.items()):
        tax_table_rows.append({
            "Canonical Skill": sk,
            "Domain Category": get_category_for_skill(sk),
            "Synonyms Count": len(syns),
            "Aliases": ", ".join(syns),
        })
    df_tax_display = pd.DataFrame(tax_table_rows)
    st.dataframe(df_tax_display, use_container_width=True, height=320, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 9: Executive & Export Center
# -----------------------------------------------------------------------------
with tab_report:
    st.markdown("### 📄 Executive Summary & Export Center")
    st.markdown("Generate presentation-ready executive briefs and export cleaned analytical datasets.")

    top_3_skills = df_freq.head(3)["skill"].tolist() if not df_freq.empty else ["N/A"]
    top_3_str = ", ".join(top_3_skills)
    top_sal_str = f"{df_salary_by_skill.iloc[0]['skill']} (${df_salary_by_skill.iloc[0]['avg_salary']:,})" if not df_salary_by_skill.empty else "N/A"
    top_cooc_str = f"{df_cooc.iloc[0]['skill_a']} + {df_cooc.iloc[0]['skill_b']}" if not df_cooc.empty else "N/A"

    report_md = f"""# Executive Job Market Skill Demand Intelligence Brief (v3.0)
**Dataset Source:** {st.session_state.data_source_label}  
**Total Postings Analyzed:** {filtered_count} (out of {raw_total} raw records, {dups_removed} duplicates removed)  
**Analysis Engine:** Skill Demand Analyzer v3.0 (Deterministic Multi-Dimensional Taxonomy Engine)  

---

## 🔑 Executive Key Takeaways & Highlights

1. **Top Demanded Skills:**
   - The top 3 most requested skills are **{top_3_str}**.
   - Primary competency **{top_skill}** is present in **{top_pct}** of all analyzed postings.

2. **Compensation Insights:**
   - The highest-paying skill in this sample is **{top_sal_str}**.
   - Overall average disclosed compensation: **{avg_comp_str}**.

3. **Leading Technical Domain:**
   - **{top_domain}** represents the largest job concentration in this dataset.

4. **Common Tech Stack Bundles:**
   - The top co-occurring skill combination is **{top_cooc_str}**.

---

## 📊 Top 10 Ranked Skills & Weighted Demand

| Rank | Skill | Domain Category | Postings Mentioning | Market Share (%) | Weighted Score |
| :---: | :--- | :--- | :---: | :---: | :---: |
"""
    for _, r in df_freq.head(10).iterrows():
        report_md += f"| {r['rank']} | {r['skill']} | {r['category']} | {r['postings_mentioning']} | {r['pct_of_postings']}% | {r['weighted_score']} |\n"

    report_md += f"""
---
*Disclaimer: This report was generated deterministically by matching job posting text against a curated skills taxonomy. Sample demo datasets reflect internal prototype distributions and do not represent empirical macroeconomic job market statistics.*
"""

    st.markdown(report_md)

    st.download_button(
        "📥 Download Executive Summary (Markdown)",
        data=report_md.encode("utf-8"),
        file_name="executive_skill_report_v3.md",
        mime="text/markdown",
    )
