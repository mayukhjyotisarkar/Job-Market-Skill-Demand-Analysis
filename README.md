# 💼 Job Market Skill Demand Analyzer (Prototype v1.0)

A beginner-friendly data analysis prototype for exploring tech job postings, extracting in-demand skills, analyzing skill co-occurrence pairs, and inspecting the actual postings behind demand statistics.

---

> [!NOTE]
> **Data Honesty & Scope Notice:**  
> This project is an exploratory **data analysis prototype**, **not a trained machine learning model**. It uses deterministic regex-based taxonomy matching.  
> The bundled `sample_postings.json` dataset contains **12 illustrative demo postings** designed for testing workflow pipelines. **Demo results must not be cited as empirical findings about current job market conditions.**

---

## 🌟 Key Features

1. **Dual Ingestion Modes:**
   - **🧪 Demo Mode:** Instant 1-click loading of bundled illustrative postings (`sample_postings.json`).
   - **📁 File Upload:** Upload any user-provided `.csv` or `.json` job postings dataset.
2. **Pre-Tagged vs. Description Extraction:**
   - Detects if postings already have skill tags (e.g. from Techmap).
   - Allows users to choose between using source tags, extracting from description text, or combining both with full origin tracking.
3. **Smart Deduplication & Preprocessing:**
   - Gracefully handles missing descriptions, empty records, and inconsistent column naming (`title` vs `job_title`, `employer` vs `company`, etc.).
   - Detects duplicate postings and tracks deduplication statistics.
4. **Interactive Skill Demand Analytics:**
   - Horizontal bar charts and ranked tables displaying both posting counts and percentages.
   - Categorized skills (Programming Languages, Data Science & AI, Cloud & DevOps, BI & Analytics, Practices, Soft Skills).
5. **Skill Co-occurrence Analysis:**
   - Identifies skills that frequently appear together in the same job requirement (e.g., *Python + SQL*, *AWS + Kubernetes*).
   - Automatically disabled for very small datasets (< 3 postings) with helpful explanations.
6. **Postings Inspector (Drill-Down):**
   - Click/select any skill or skill pair to immediately view all matching job postings, complete with badges, company info, and full descriptions.
7. **Live Editable Taxonomy:**
   - Add new custom skills or aliases on the fly directly inside the web UI.
8. **Exportable Results:**
   - Download ranked skill frequencies (CSV), co-occurrence pairs (CSV), and enriched postings (JSON/CSV).
9. **Optional Live API Ingestion:**
   - CLI script (`ingest.py`) supporting Techmap and JSearch (RapidAPI) with `.env` secret management.

---

## 📂 Project Structure

```text
Job Market Analysis/
├── app.py                     # Main Streamlit web application
├── taxonomy.py                # Skill taxonomy dictionary, categories, and synonym aliases
├── extract_analyze.py         # Regex extraction engine, deduplication, frequency & co-occurrence
├── ingest.py                  # Live API ingestion script (Techmap & JSearch)
├── test_pipeline.py           # Automated test suite
├── requirements.txt           # Python package dependencies
├── .env.example               # Template for optional API credentials
├── .gitignore                 # Excludes secrets, temporary files, and caches
├── sample_postings.json       # Bundled illustrative demo data (JSON)
├── sample_postings.csv        # Bundled illustrative demo data (CSV)
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

### 4. Run the Automated Tests
```bash
python test_pipeline.py
```

### 5. Launch the Streamlit Web App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to use the application!

---

## 📄 Input Data Formats

The app accepts `.json` and `.csv` files. It automatically normalizes common column naming variations:

### JSON Format Example:
```json
[
  {
    "title": "Senior Data Scientist",
    "company": "Fintech Solutions",
    "posted_at": "2026-09-20",
    "description": "Looking for a Data Scientist strong in Python, SQL, and PyTorch for machine learning pipelines."
  }
]
```

### CSV Format Example:
| title | company | posted_at | description |
| :--- | :--- | :--- | :--- |
| Senior Data Scientist | Fintech Solutions | 2026-09-20 | Looking for a Data Scientist strong in Python, SQL, and PyTorch... |

### Optional Fields Supported:
- `skills_raw` or `skills` or `tags`: Pre-extracted array or comma-separated string of skills.
- `job_title`, `employer_name`, `job_description`, `dateCreated`.

---

## 📡 Live API Ingestion (Optional)

If your team wishes to collect live postings from API providers:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your API credentials into `.env`:
   - `TECHMAP_API_KEY`: For Techmap (free tier: ~1,000 jobs/mo, pre-tagged skills).
   - `RAPIDAPI_KEY`: For JSearch on RapidAPI (free tier: ~200 requests/mo, Google for Jobs aggregator).
3. Run the ingestion script:
   ```bash
   # Ingest from Techmap
   python ingest.py --source techmap --query "data engineer" --pages 2

   # Ingest from JSearch
   python ingest.py --source jsearch --query "machine learning" --pages 2
   ```
4. Ingested files are saved to `raw_postings/` and can be uploaded directly into the web application.

---

## 🤝 Sharing & Team Collaboration (Git)

To share this prototype with teammates via a Git repository:

1. Initialize Git and stage your files:
   ```bash
   git init
   git add .
   git commit -m "feat: Initial working prototype of Skill Demand Analyzer"
   ```
2. Connect to your team's remote repository:
   ```bash
   git remote add origin <TEAM_REPOSITORY_URL>
   git branch -M main
   git push -u origin main
   ```
3. **Safety Checklist:**
   - Ensure `.env` is listed in `.gitignore` (already configured).
   - Do **not** publish or deploy the app to public cloud hosting without prior alignment.

---

## ⚠️ Known Limitations & Future Roadmap

- **Keyword Matching vs. Context:** Regex matching does not distinguish between required vs. preferred skills (e.g. "5+ years Python required" vs "knowledge of Python is a plus").
- **Taxonomy Breadth:** The prototype contains ~35 canonical skills across 6 domains. Future iterations can integrate standard taxonomies like [ESCO (European Skills, Competences, Qualifications and Occupations)](https://esco.ec.europa.eu/) or [Lightcast Open Skills](https://lightcast.io/open-skills), or libraries like `skillNer`.
- **Sample Representativeness:** Small or domain-specific datasets (e.g. 12 demo postings) show internal frequencies only and do not extrapolate to the broader economy.
