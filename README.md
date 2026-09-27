# 💼 Job Market Skill Demand Analyzer (v2.0)

A powerful, beginner-friendly exploratory data analysis application for tech job postings. Analyzes skill demand, role-domain and seniority matrices, skill co-occurrence clustering, and candidate skill gap matching using deterministic taxonomy extraction.

---

> [!NOTE]
> **Data Honesty & Scope Notice:**  
> This project is an exploratory **data analysis prototype**, **not a trained machine learning model**. It uses deterministic regex-based taxonomy matching.  
> The bundled `sample_postings.json` dataset contains **25 illustrative demo postings** designed for testing workflow pipelines. **Demo results must not be cited as empirical findings about current job market conditions.**

---

## 🌟 What's New in v2.0

| Feature Area | v1.0 Baseline | v2.0 Enhanced |
| :--- | :--- | :--- |
| **Taxonomy Vocabulary** | ~35 skills | **120+ curated tech skills** across 8 structured domains |
| **Domain & Seniority Matrix** | None | Automatic classification of **Role Domains** and **Seniority Levels** with interactive cross-tab heatmaps |
| **Candidate Skill Gap Matcher** | None | Input your skills profile -> calculates **Market Match Rate** & ranks **Highest-Impact Missing Skills** |
| **Visual In-line Highlighting** | Plain code block | **In-line color-coded HTML highlighting** with tooltips for every matched skill in job descriptions |
| **Co-occurrence Correlation** | Basic pair count | Added **Jaccard Correlation Similarity** scores and tech stack combinations |
| **Taxonomy Management** | UI additions reset on reload | **Taxonomy Presets**, Export active taxonomy as JSON, and Upload custom taxonomy files |
| **Executive Reporting** | Raw CSV exports | Automated **Executive Summary Markdown Report Generator** with one-click export |
| **Ingestion Support** | JSON & basic CSV | JSON, CSV, TSV, XLSX, and **Direct Free-Text Paste** with automatic deduplication audit |

---

## 📂 Project Architecture

```text
Job Market Analysis/
├── app.py                     # Streamlit v2 application (7 analytics tabs)
├── taxonomy.py                # 120+ skills taxonomy, categories, and preset bundles
├── extract_analyze.py         # Multi-dimensional extraction, matrices, gap matching & highlighter
├── ingest.py                  # Live API ingestion script (Techmap & JSearch)
├── test_pipeline.py           # Automated test suite (v2)
├── requirements.txt           # Python package dependencies
├── .env.example               # Template for optional API credentials
├── .gitignore                 # Excludes secrets, temporary files, and caches
├── sample_postings.json       # 25 bundled illustrative demo postings (JSON)
├── sample_postings.csv        # 25 bundled illustrative demo postings (CSV)
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

## 📊 Application Tour & Tabs

1. **📊 Skill Demand Overview:** Interactive horizontal bar charts and ranked tables showing postings counts, market percentages, and category filters.
2. **🏢 Role & Seniority Matrix:** Heatmaps and cross-tabulations showing how skill demand differs between *Data Science*, *Data Engineering*, *Backend*, *DevOps*, etc., and between *Junior* vs *Senior* roles.
3. **🔗 Co-occurrence & Stack Clusters:** Discover which skills are frequently paired together (e.g. *Python + SQL*, *AWS + Kubernetes*) with Jaccard similarity metrics.
4. **🎯 Candidate Skill Gap & Matcher:** Select or paste your current skillset to view your **50%+ and 80%+ Job Match Rates** and view the **top missing skills** that unlock the most jobs.
5. **🔍 Interactive Postings Inspector:** Filter by skill, seniority, or role to view job cards with **in-line colored skill highlighting** inside the full job descriptions.
6. **⚙️ Taxonomy Studio:** Switch taxonomy presets, add custom skills on the fly, export your taxonomy to JSON, or upload a custom taxonomy file.
7. **📄 Executive Report:** Generates a ready-to-share Markdown executive summary report summarizing all findings.

---

## 📄 Input Data Formats

The app accepts `.json`, `.csv`, `.tsv`, `.xlsx`, or raw text pastes. Common column headers are automatically mapped:
- **Title:** `title`, `job_title`, `position`
- **Company:** `company`, `employer_name`, `employer`
- **Description:** `description`, `job_description`, `text`, `summary`
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
git commit -m "feat: release v2.0 of job market skill demand analyzer"
git push origin main
```

---

## ⚠️ Known Limitations & Future Roadmap

- **Keyword Matching vs. Deep Semantic Parsing:** The prototype does not distinguish between strict requirements and minor mentions without section headers.
- **Taxonomy Breadth:** While expanded to 120+ skills, specialized niche domains can be further supplemented by uploading custom taxonomy JSON files.
- **Sample Representativeness:** Small datasets reflect internal sample frequencies only and cannot be generalized to the entire macro economy.
