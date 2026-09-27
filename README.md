# 💼 Job Market Skill Demand Analyzer (v3.0 Enterprise Intelligence Edition)

A comprehensive data analysis application for tech job postings. Analyzes skill demand, compensation benchmarks, role/seniority matrices, A/B cohort comparisons, and structured career roadmaps using deterministic multi-dimensional taxonomy matching.

---

> [!NOTE]
> **Data Honesty & Scope Notice:**  
> This project is an exploratory **data analysis prototype**, **not a trained machine learning model**. It uses deterministic regex-based taxonomy matching.  
> The bundled `sample_postings.json` dataset contains **40 illustrative demo postings** with compensation ranges and experience requirements. **Demo results must not be cited as empirical findings about current job market conditions.**

---

## 🌟 Evolution & Feature Matrix: v1.0 vs v2.0 vs v3.0

| Feature Area | v1.0 Baseline | v2.0 Enhanced | v3.0 Enterprise Edition |
| :--- | :--- | :--- | :--- |
| **Taxonomy Scope** | ~35 skills | 120+ skills | **180+ curated skills across 10 specialized domains** (aligned with ESCO / O*NET) |
| **Compensation Intelligence** | None | None | **Salary parser ($110k–$260k, hourly-to-annual normalization) & Top-Paying Skills Leaderboard** |
| **Weighted Demand Scoring** | Raw counts only | Raw counts only | **Distinguishes Required vs Preferred skills with weighted demand scoring** |
| **A/B Cohort Comparison Studio** | None | None | **Side-by-side cohort comparison** (Remote vs Onsite, Senior vs Junior, Domain A vs Domain B) with relative lift |
| **Experience & Degree Extraction** | None | Basic Seniority | **Extracts Min Years of Experience & Education Levels** (Bachelor's, Master's, PhD, Bootcamp) |
| **Structured Career Roadmap** | Raw missing count | Missing skills list | **4-Phase Structured Milestone Roadmap** (Foundation → Core Stack → Cloud/Scale → Leadership) |
| **Interactive Postings Inspector** | Plain text box | HTML highlighted text | **In-line color-coded HTML highlighting with salary badges, experience chips, & domain tags** |
| **Export & Reporting Center** | Basic CSV | Basic Markdown | **Presentation-ready Executive Summary Markdown report + Clean CSV/JSON export suite** |
| **Bundled Demo Dataset** | 12 postings | 25 postings | **40 comprehensive postings** covering salaries, experience, degrees, and work models |

---

## 📂 Project Architecture

```text
Job Market Analysis/
├── app.py                     # Streamlit v3 application (9 analytical tabs)
├── taxonomy.py                # 180+ skills taxonomy, 10 domains, ESCO alignments, and preset bundles
├── extract_analyze.py         # Multi-dimensional extraction, salary intelligence, A/B cohorts, and roadmaps
├── ingest.py                  # Live API ingestion script (Techmap & JSearch)
├── test_pipeline.py           # Automated test suite (v3)
├── requirements.txt           # Python package dependencies
├── .env.example               # Template for optional API credentials
├── .gitignore                 # Excludes secrets, temporary files, and caches
├── sample_postings.json       # 40 bundled illustrative demo postings (JSON)
├── sample_postings.csv        # 40 bundled illustrative demo postings (CSV)
├── data/                      # Example datasets for testing
│   ├── sample_postings.json
│   ├── sample_postings.csv
│   └── sample_with_tags.json  # Pre-tagged skills schema example
└── README.md                  # Project documentation & teammate guide
```

---

## 🚀 Quickstart Guide for Teammates

### 1. Prerequisites
- Python 3.9 or higher (tested on Python 3.10–3.14).

### 2. Setup Virtual Environment (Recommended)
```bash
# Clone or navigate to the repository
cd "Job Market Analysis"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Automated Tests
```bash
python test_pipeline.py
```

### 5. Launch the Streamlit Web App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to use the application.

---

## 📊 9 Application Tabs Overview

1. **📊 Skill Demand & Weighted Priority:** Market share percentage vs weighted demand score (accounting for Required vs Preferred mentions).
2. **💰 Salary & Compensation Analytics:** Top-paying technical skills leaderboard, average salary per skill, and sample compensation distributions.
3. **🏢 Role, Seniority & Experience Matrix:** Cross-tabulation heatmaps of skills across job domains, experience levels, and minimum degree requirements.
4. **⚖️ A/B Cohort Comparison Studio:** Compare skill demand between two segments (e.g., Remote vs Hybrid, Senior vs Junior) with relative percentage lift.
5. **🔗 Co-occurrence & Stack Clusters:** Discover which skills are frequently paired together (e.g. *Python + SQL*, *AWS + Kubernetes*) with Jaccard similarity metrics.
6. **🎯 Career Roadmap & Candidate Matcher:** Input your current skillset to calculate **50%+ & 80%+ Job Match Coverage** and generate a **4-Phase Structured Learning Roadmap** toward your target domain.
7. **🔍 Postings Inspector:** Search and drill down into job postings with **in-line colored skill highlighting**, salary badges, and experience chips.
8. **⚙️ Taxonomy & ESCO Studio:** Switch taxonomy presets, add custom skills, export active taxonomy as JSON, or upload a custom taxonomy file.
9. **📄 Executive & Export Center:** Generates a ready-to-share Executive Summary Markdown report and provides one-click downloads for all analytical tables.

---

## 📄 Input Data Formats

The app accepts `.json`, `.csv`, `.tsv`, `.xlsx`, or raw text pastes. Common column headers are automatically mapped:
- **Title:** `title`, `job_title`, `position`
- **Company:** `company`, `employer_name`, `employer`
- **Description:** `description`, `job_description`, `text`, `summary`
- **Salary (optional):** `salary`, `compensation`, `salary_range`
- **Tags (optional):** `skills_raw`, `skills`, `tags`
- **Date / Location (optional):** `posted_at`, `date`, `country`, `location`

---

## 📡 Live API Ingestion (Optional)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Insert your free API keys into `.env`:
   - `TECHMAP_API_KEY`: For Techmap (free tier: ~1,000 jobs/mo, pre-tagged skills).
   - `RAPIDAPI_KEY`: For JSearch on RapidAPI (free tier: ~200 requests/mo).
3. Run the CLI ingestion script:
   ```bash
   python ingest.py --source techmap --query "data engineer" --pages 2
   ```

---

## 🤝 Sharing & Team Collaboration (Git)

```bash
git add .
git commit -m "feat: release v3.0 enterprise intelligence edition"
git push origin main
```
