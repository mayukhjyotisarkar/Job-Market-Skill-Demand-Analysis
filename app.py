"""
Skill Demand Analyzer - Streamlit Prototype Application

A beginner-friendly data analysis prototype for analyzing job postings,
extracting skill demand via an editable taxonomy, exploring co-occurrences,
and inspecting postings behind findings.
"""

import os
import json
import io
import copy
from typing import Dict, List, Any, Optional

import streamlit as st
import pandas as pd
import altair as alt

from taxonomy import (
    DEFAULT_SKILL_SYNONYMS,
    SKILL_CATEGORIES,
    get_default_taxonomy,
    get_category_for_skill,
)
from extract_analyze import (
    build_skill_frame,
    deduplicate_postings,
    skill_frequency,
    skill_cooccurrence,
    filter_postings,
    get_postings_for_skill,
    get_postings_for_pair,
)

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Skill Demand Analyzer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #475569;
        margin-top: 2px;
    }
    .demo-badge {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        border: 1px solid #FDE68A;
        margin-bottom: 8px;
    }
    .live-badge {
        display: inline-block;
        background-color: #DCFCE7;
        color: #166534;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        border: 1px solid #BBF7D0;
        margin-bottom: 8px;
    }
    .tag-badge {
        display: inline-block;
        background-color: #EEF2FF;
        color: #3730A3;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        margin: 2px 3px 2px 0;
        border: 1px solid #C7D2FE;
    }
    .source-tag-badge {
        display: inline-block;
        background-color: #F0FDF4;
        color: #166534;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        margin: 2px 3px 2px 0;
        border: 1px solid #BBF7D0;
    }
    .disclaimer-box {
        background-color: #F1F5F9;
        border-left: 4px solid #64748B;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #334155;
        margin-bottom: 1.2rem;
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
    st.session_state.data_source_label = "Illustrative Demo Data"

if "is_demo" not in st.session_state:
    st.session_state.is_demo = True


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
@st.cache_data
def load_sample_demo_data() -> List[Dict[str, Any]]:
    """Load the default sample_postings.json bundled with the project."""
    paths_to_check = [
        "sample_postings.json",
        os.path.join("data", "sample_postings.json"),
        os.path.join("zip", "sample_postings.json"),
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


def parse_uploaded_file(uploaded_file) -> Tuple[List[Dict[str, Any]], str]:
    """Parse an uploaded CSV or JSON file into standard list of dictionaries."""
    try:
        filename = uploaded_file.name
        content = uploaded_file.getvalue()

        if filename.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                return data, filename
            elif isinstance(data, dict) and "result" in data:
                return data["result"], filename
            elif isinstance(data, dict) and "data" in data:
                return data["data"], filename
            else:
                return [data], filename
        elif filename.lower().endswith(".csv"):
            df = pd.read_csv(io.StringIO(content.decode("utf-8")))
            # Replace NaN with empty string
            df = df.fillna("")
            return df.to_dict(orient="records"), filename
        else:
            raise ValueError(f"Unsupported file extension. Please upload a .json or .csv file.")
    except Exception as exc:
        st.error(f"Error reading file '{uploaded_file.name}': {exc}")
        return [], ""


# -----------------------------------------------------------------------------
# Sidebar: Data Source & Filtering
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/briefcase.png", width=54)
    st.title("Data & Settings")

    st.markdown("### 1. Data Source")
    data_choice = st.radio(
        "Select Data Input:",
        ["🧪 Sample Demo Data", "📁 Upload File (CSV / JSON)"],
        index=0 if st.session_state.is_demo else 1,
        help="Use built-in illustrative postings or upload your own dataset."
    )

    if data_choice == "🧪 Sample Demo Data":
        st.session_state.is_demo = True
        st.session_state.data_source_label = "sample_postings.json (Illustrative Demo)"
        raw_data = load_sample_demo_data()
        st.session_state.raw_postings = raw_data
        st.info("💡 **Demo Mode Active**: 12 illustrative tech job postings loaded.")
    else:
        st.session_state.is_demo = False
        uploaded = st.file_uploader(
            "Upload Job Postings (.json or .csv)",
            type=["json", "csv"],
            help="File can contain fields: title, company, description, and optional skills_raw/tags."
        )
        if uploaded is not None:
            parsed, fname = parse_uploaded_file(uploaded)
            if parsed:
                st.session_state.raw_postings = parsed
                st.session_state.data_source_label = f"Uploaded File: {fname}"
                st.success(f"Loaded {len(parsed)} records from `{fname}`.")
        else:
            st.warning("Please upload a file or switch to Demo Data.")
            st.session_state.raw_postings = []
            st.session_state.data_source_label = "No file loaded"

    st.markdown("---")

    # Extraction Configuration
    st.markdown("### 2. Skill Extraction Mode")
    skill_mode = st.selectbox(
        "Skill Source Handling:",
        [
            "Auto (Use tags if present, else extract)",
            "Extracted from Description Only",
            "Source Pre-Tags Only",
            "Combined (Tags + Extracted)",
        ],
        index=0,
        help="Choose whether to prioritize source-provided skill tags, text regex extraction, or both."
    )
    mode_map = {
        "Auto (Use tags if present, else extract)": "auto",
        "Extracted from Description Only": "extracted_only",
        "Source Pre-Tags Only": "source_tags_only",
        "Combined (Tags + Extracted)": "combined",
    }
    selected_mode = mode_map[skill_mode]

    # Deduplication Toggle
    dedup_toggle = st.checkbox(
        "Enable Posting Deduplication",
        value=True,
        help="Identifies duplicate postings sharing title, company, and description prefix."
    )

    st.markdown("---")
    st.markdown("### 3. About this Prototype")
    st.caption(
        "**Skill Demand Analyzer v1.0**\n\n"
        "• Deterministic regex-based taxonomy matching.\n"
        "• Built for beginner-friendly exploratory data analysis.\n"
        "• No machine learning or generative models used."
    )


# -----------------------------------------------------------------------------
# Main Application Content
# -----------------------------------------------------------------------------

# Header Area
st.markdown('<div class="main-header">Job Market Skill Demand Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Analyze job postings, discover frequently requested skills, and inspect underlying postings.</div>', unsafe_allow_html=True)

# Honesty & Data Source Status Banner
if st.session_state.is_demo:
    st.markdown(
        """
        <div class="disclaimer-box">
            <span class="demo-badge">🧪 DEMO DATASET</span>
            <strong>Illustrative Sample Data:</strong> The results below are derived from 
            <code>sample_postings.json</code> (12 sample postings) for demonstration and workflow verification. 
            <strong>They do not represent real-time job market trends or empirical labor statistics.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="disclaimer-box">
            <span class="live-badge">📁 USER DATASET</span>
            <strong>Active Dataset:</strong> <code>{st.session_state.data_source_label}</code>.
            Skills are extracted deterministically based on the configurable taxonomy.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Validate data presence
raw_data = st.session_state.raw_postings
if not raw_data:
    st.warning("👈 No postings loaded. Please choose **Sample Demo Data** or upload a valid `.csv`/`.json` file in the sidebar.")
    st.stop()

# Processing & Deduplication
raw_count = len(raw_data)
if dedup_toggle:
    deduped_data, dup_removed = deduplicate_postings(raw_data)
else:
    deduped_data = raw_data
    dup_removed = 0

# Build Enriched DataFrame
df_all = build_skill_frame(
    deduped_data,
    taxonomy_dict=st.session_state.taxonomy,
    skill_source_mode=selected_mode,
)

# Detect data characteristics
has_source_tags_count = int(df_all["has_source_tags"].sum())
has_missing_desc_count = int((~df_all["has_description"]).sum())
analyzed_count = len(df_all)

# -----------------------------------------------------------------------------
# Global Filters Bar
# -----------------------------------------------------------------------------
with st.expander("🔍 **Filters & Search** (Job Title, Company, Keyword)", expanded=True):
    fcol1, fcol2, fcol3 = st.columns([1.5, 1.2, 1.3])

    # Available Titles
    available_titles = sorted(list(set(df_all["title"].dropna().tolist())))
    available_companies = sorted(list(set(df_all["company"].dropna().tolist())))

    with fcol1:
        selected_titles = st.multiselect(
            "Filter by Job Title:",
            options=available_titles,
            default=[],
            placeholder="All Job Titles (Select to filter...)",
        )

    with fcol2:
        selected_companies = st.multiselect(
            "Filter by Company:",
            options=available_companies,
            default=[],
            placeholder="All Companies...",
        )

    with fcol3:
        search_kw = st.text_input(
            "Keyword Search:",
            placeholder="Search in title, description, skills...",
        )

# Apply filters
df_filtered = filter_postings(
    df_all,
    selected_titles=selected_titles if selected_titles else None,
    keyword=search_kw if search_kw else None,
    selected_companies=selected_companies if selected_companies else None,
)

filtered_count = len(df_filtered)

# Compute Analysis Metrics & Tables
df_freq = skill_frequency(df_filtered)
df_cooc = skill_cooccurrence(df_filtered, top_n=12, min_cooc=1)

# Summary Key Performance Metrics
mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)

with mcol1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Postings Analyzed</div>
            <div class="metric-value">{filtered_count}</div>
            <div class="metric-sub">{raw_count} raw ({dup_removed} dupes removed)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol2:
    unique_skills_count = len(df_freq)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Unique Skills</div>
            <div class="metric-value">{unique_skills_count}</div>
            <div class="metric-sub">Matched from taxonomy</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol3:
    top_skill_name = df_freq.iloc[0]["skill"] if not df_freq.empty else "N/A"
    top_skill_pct = f"{df_freq.iloc[0]['pct_of_postings']}%" if not df_freq.empty else "0%"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Top Demanded Skill</div>
            <div class="metric-value">{top_skill_name}</div>
            <div class="metric-sub">In {top_skill_pct} of filtered postings</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol4:
    avg_skills = round(df_filtered["skill_count"].mean(), 1) if not df_filtered.empty else 0.0
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Avg Skills / Job</div>
            <div class="metric-value">{avg_skills}</div>
            <div class="metric-sub">Skills per posting</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol5:
    source_tag_info = f"{has_source_tags_count} tagged" if has_source_tags_count > 0 else "Extracted text"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Data Sourcing</div>
            <div class="metric-value" style="font-size: 1.25rem;">{selected_mode.capitalize()}</div>
            <div class="metric-sub">{source_tag_info}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main Tabs Layout
# -----------------------------------------------------------------------------
tab_overview, tab_cooc, tab_inspector, tab_taxonomy, tab_api_guide = st.tabs([
    "📊 Skill Demand Overview",
    "🔗 Skill Co-occurrence Pairs",
    "🔍 Postings Inspector (Drill-down)",
    "⚙️ Editable Taxonomy",
    "📡 Live API & Ingestion Guide",
])

# -----------------------------------------------------------------------------
# TAB 1: Skill Demand Overview
# -----------------------------------------------------------------------------
with tab_overview:
    if df_filtered.empty:
        st.info("No postings matched the current filter criteria. Try adjusting or clearing filters.")
    else:
        col_chart, col_table = st.columns([1.3, 1.0])

        with col_chart:
            st.markdown("### 📈 Top Demanded Skills")
            
            # Slider for top N skills to visualize
            max_n = min(30, max(5, len(df_freq)))
            top_n = st.slider("Number of skills to display:", min_value=5, max_value=max_n, value=min(15, max_n))

            top_skills_df = df_freq.head(top_n).copy()

            if not top_skills_df.empty:
                # Altair Horizontal Bar Chart
                chart = (
                    alt.Chart(top_skills_df)
                    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                    .encode(
                        x=alt.X("pct_of_postings:Q", title="% of Job Postings", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("skill:N", sort="-x", title="Canonical Skill"),
                        color=alt.Color(
                            "category:N",
                            title="Category",
                            scale=alt.Scale(scheme="category10"),
                        ),
                        tooltip=[
                            alt.Tooltip("skill:N", title="Skill"),
                            alt.Tooltip("category:N", title="Category"),
                            alt.Tooltip("postings_mentioning:Q", title="Postings Mentioning"),
                            alt.Tooltip("pct_of_postings:Q", title="% of Total"),
                        ],
                    )
                    .properties(height=max(320, top_n * 24))
                    .configure_axis(grid=True, gridDash=[2, 2], gridColor="#E2E8F0")
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No skill matches found for this selection.")

        with col_table:
            st.markdown("### 📋 Ranked Skill Demand Table")

            # Category filter for table
            categories = ["All Categories"] + sorted(list(df_freq["category"].unique()))
            selected_cat = st.selectbox("Filter table by category:", categories)

            df_table = df_freq.copy()
            if selected_cat != "All Categories":
                df_table = df_table[df_table["category"] == selected_cat]

            st.dataframe(
                df_table[[
                    "rank",
                    "skill",
                    "category",
                    "postings_mentioning",
                    "pct_of_postings",
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

            # Export Button
            csv_data = df_table.to_csv(index=False).encode("utf-8")
            source_tag = "demo" if st.session_state.is_demo else "uploaded"
            st.download_button(
                label="📥 Download Skill Frequency CSV",
                data=csv_data,
                file_name=f"skill_frequency_{source_tag}.csv",
                mime="text/csv",
                help="Exports the ranked skill table including posting counts and percentages."
            )


# -----------------------------------------------------------------------------
# TAB 2: Skill Co-occurrence
# -----------------------------------------------------------------------------
with tab_cooc:
    st.markdown("### 🔗 Common Skill Pairings (Co-occurrence)")
    
    # Requirement: Show common skill pairs only when dataset has enough postings to make that view useful
    MIN_POSTINGS_FOR_COOC = 3

    if filtered_count < MIN_POSTINGS_FOR_COOC:
        st.info(
            f"ℹ️ **Skill co-occurrence analysis is disabled for small samples (< {MIN_POSTINGS_FOR_COOC} postings).**\n\n"
            f"Currently analyzing {filtered_count} posting(s). Co-occurrence pairings require sufficient posting volume "
            f"to establish meaningful correlation patterns. Please load a larger dataset or broaden your filters."
        )
    elif df_cooc.empty:
        st.warning("No co-occurring skill pairs were found within the filtered postings.")
    else:
        st.markdown(
            "Skill co-occurrence identifies pairs of competencies that frequently appear together in the same job requirements. "
            "This highlights common tech stack combinations (e.g., *Python + SQL*, *AWS + Kubernetes*)."
        )

        col_c1, col_c2 = st.columns([1.2, 1.0])

        with col_c1:
            st.markdown("#### Top Co-occurring Pairs")
            top_pairs = df_cooc.head(12).copy()
            top_pairs["pair_label"] = top_pairs["skill_a"] + " + " + top_pairs["skill_b"]

            chart_cooc = (
                alt.Chart(top_pairs)
                .mark_bar(color="#4F46E5", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    x=alt.X("co_occurrences:Q", title="Co-occurrences (Job Postings)"),
                    y=alt.Y("pair_label:N", sort="-x", title="Skill Combination"),
                    tooltip=[
                        alt.Tooltip("pair_label:N", title="Skill Pair"),
                        alt.Tooltip("co_occurrences:Q", title="Co-occurrences"),
                        alt.Tooltip("pct_of_postings:Q", title="% of Total Postings"),
                    ],
                )
                .properties(height=360)
            )
            st.altair_chart(chart_cooc, use_container_width=True)

        with col_c2:
            st.markdown("#### Co-occurrence Matrix Data")
            st.dataframe(
                df_cooc[[
                    "skill_a",
                    "skill_b",
                    "co_occurrences",
                    "pct_of_postings",
                ]].rename(columns={
                    "skill_a": "Skill 1",
                    "skill_b": "Skill 2",
                    "co_occurrences": "Shared Postings",
                    "pct_of_postings": "% of Postings",
                }),
                use_container_width=True,
                hide_index=True,
                height=360,
            )

            cooc_csv = df_cooc.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Co-occurrence CSV",
                data=cooc_csv,
                file_name="skill_cooccurrence.csv",
                mime="text/csv",
            )


# -----------------------------------------------------------------------------
# TAB 3: Postings Inspector (Drill-Down)
# -----------------------------------------------------------------------------
with tab_inspector:
    st.markdown("### 🔍 Drill-Down: Inspect Postings Behind Results")
    st.markdown(
        "Select a skill or skill combination to see all the individual job postings that mention it, "
        "including company details, metadata, and extracted versus source-tagged skills."
    )

    drill_col1, drill_col2 = st.columns([1.5, 1.5])

    all_available_skills = sorted(list(df_freq["skill"].unique())) if not df_freq.empty else []

    with drill_col1:
        inspected_skill = st.selectbox(
            "Select Skill to Inspect:",
            options=["(Show All Postings)"] + all_available_skills,
            index=1 if len(all_available_skills) > 0 else 0,
        )

    with drill_col2:
        secondary_skill = st.selectbox(
            "Optional: Combine with Second Skill (Intersection):",
            options=["(None)"] + all_available_skills,
            index=0,
        )

    # Filter postings for inspection
    if inspected_skill != "(Show All Postings)":
        if secondary_skill != "(None)":
            matching_postings_df = get_postings_for_pair(df_filtered, inspected_skill, secondary_skill)
            label_text = f"postings mentioning both **'{inspected_skill}'** and **'{secondary_skill}'**"
        else:
            matching_postings_df = get_postings_for_skill(df_filtered, inspected_skill)
            label_text = f"postings mentioning **'{inspected_skill}'**"
    else:
        matching_postings_df = df_filtered
        label_text = "total postings in current filter"

    st.markdown(f"Found **{len(matching_postings_df)}** {label_text}:")

    if matching_postings_df.empty:
        st.info("No postings match this specific skill combination.")
    else:
        for _, row in matching_postings_df.iterrows():
            with st.container():
                st.markdown(f"#### 📌 {row['title']} — *{row['company']}*")
                
                # Meta badges
                c_badges = []
                c_badges.append(f"📅 **Posted:** {row['posted_at']}")
                c_badges.append(f"🏷️ **Skill Origin:** `{row['skill_origin']}`")
                st.markdown(" &nbsp;|&nbsp; ".join(c_badges))

                # Render Skills as Badges
                skills_list = row["skills"]
                if skills_list:
                    badges_html = "".join([f'<span class="tag-badge">{s}</span>' for s in skills_list])
                    st.markdown(f"**Identified Skills ({len(skills_list)}):**<br>{badges_html}", unsafe_allow_html=True)
                else:
                    st.markdown("*No taxonomy skills detected in this posting.*")

                # Expandable Full Description
                with st.expander("📄 View Job Description"):
                    desc = row["description"]
                    if desc:
                        st.markdown(f"```text\n{desc}\n```")
                    else:
                        st.caption("*No description provided for this record.*")

                st.markdown("---")

        # Full export of analyzed postings
        enriched_json = matching_postings_df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            label="📥 Download Analyzed Postings (JSON)",
            data=enriched_json,
            file_name="analyzed_postings.json",
            mime="application/json",
        )


# -----------------------------------------------------------------------------
# TAB 4: Editable Taxonomy
# -----------------------------------------------------------------------------
with tab_taxonomy:
    st.markdown("### ⚙️ Skills Taxonomy & Synonym Management")
    st.markdown(
        "The prototype matches skill demand by matching job text against canonical skills and their surface-form synonyms. "
        "You can inspect, add custom skills, or customize alias terms below."
    )

    tcol1, tcol2 = st.columns([1.2, 1.0])

    with tcol1:
        st.markdown("#### Add New Skill / Synonyms")
        with st.form("add_skill_form"):
            new_skill = st.text_input("Canonical Skill Name (e.g. 'Rust', 'GraphQL', 'Snowflake'):")
            new_aliases = st.text_area(
                "Aliases / Surface Forms (comma-separated):",
                placeholder="e.g., rust, rust-lang, rustlang",
            )
            submit_skill = st.form_submit_button("➕ Add / Update Skill")

            if submit_skill:
                if new_skill.strip() and new_aliases.strip():
                    aliases = [a.strip() for a in new_aliases.split(",") if a.strip()]
                    st.session_state.taxonomy[new_skill.strip()] = aliases
                    st.success(f"Added skill '{new_skill.strip()}' with {len(aliases)} synonyms!")
                    st.rerun()
                else:
                    st.error("Please provide both a canonical skill name and at least one synonym alias.")

        if st.button("🔄 Reset Taxonomy to Default"):
            st.session_state.taxonomy = get_default_taxonomy()
            st.success("Taxonomy reset to defaults.")
            st.rerun()

    with tcol2:
        st.markdown("#### Current Taxonomy Overview")
        tax_rows = []
        for sk, syns in st.session_state.taxonomy.items():
            tax_rows.append({
                "Canonical Skill": sk,
                "Category": get_category_for_skill(sk),
                "Synonyms Count": len(syns),
                "Synonym List": ", ".join(syns),
            })
        df_tax = pd.DataFrame(tax_rows)
        st.dataframe(df_tax[["Canonical Skill", "Category", "Synonyms Count", "Synonym List"]], height=380, hide_index=True)


# -----------------------------------------------------------------------------
# TAB 5: Live API & Ingestion Guide
# -----------------------------------------------------------------------------
with tab_api_guide:
    st.markdown("### 📡 Live Data Sourcing & API Ingestion")
    st.markdown(
        """
        The prototype is designed to work in two modes:
        1. **Offline / Demo / Upload Mode** (Default): Upload your own `.csv`/`.json` or use `sample_postings.json`.
        2. **Live API Mode** (Via CLI / `.env`): Pull fresh postings using supported job posting aggregators.

        ---
        #### Configured Ingestion APIs in `ingest.py`:

        | Source | Description | Pre-tagged Skills? | Free Tier Allowance |
        | :--- | :--- | :--- | :--- |
        | **Techmap Jobs API** | Structured tech job postings | ✅ Yes (`skills` array) | ~1,000 jobs/month |
        | **JSearch (RapidAPI)** | Aggregates Google for Jobs, Indeed, LinkedIn | ❌ No (extracted from text) | ~200 requests/month |

        ---
        #### How to Ingest Live Postings:

        1. Copy `.env.example` to `.env`:
           ```bash
           cp .env.example .env
           ```
        2. Insert your free API keys into `.env`:
           ```ini
           TECHMAP_API_KEY=your_key_here
           RAPIDAPI_KEY=your_key_here
           ```
        3. Run `ingest.py` from your terminal:
           ```bash
           # Using Techmap (pre-tagged skills)
           python ingest.py --source techmap --query "data scientist" --pages 2

           # Using JSearch (free-text description extraction)
           python ingest.py --source jsearch --query "software engineer" --pages 2
           ```
        4. The normalized JSON will be saved into `raw_postings/` and can be uploaded directly into this web app!
        """
    )
