"""
Starter skills taxonomy + synonym map organized by category.

This stands in for ESCO / Lightcast Open Skills for the prototype. In future
iterations, this dictionary can be expanded, edited through the UI, or replaced
with automated skill extractors (e.g., skillNer, Nesta ojd_daps_skills).
"""

import copy

# Canonical Skill -> Category Mapping
SKILL_CATEGORIES = {
    # Languages
    "Python": "Programming Languages",
    "SQL": "Programming Languages",
    "R": "Programming Languages",
    "Java": "Programming Languages",
    "JavaScript": "Programming Languages",
    "TypeScript": "Programming Languages",
    "C++": "Programming Languages",
    "C": "Programming Languages",
    "C#": "Programming Languages",
    "Go": "Programming Languages",
    "Rust": "Programming Languages",

    # AI / Machine Learning & Data Science
    "Machine learning": "Data Science & AI",
    "Deep learning": "Data Science & AI",
    "NLP": "Data Science & AI",
    "Computer vision": "Data Science & AI",
    "TensorFlow": "Data Science & AI",
    "PyTorch": "Data Science & AI",
    "scikit-learn": "Data Science & AI",
    "Pandas": "Data Science & AI",
    "NumPy": "Data Science & AI",
    "Statistics": "Data Science & AI",
    "LLM / RAG": "Data Science & AI",

    # Cloud, Infra & DevOps
    "AWS": "Cloud & DevOps",
    "Azure": "Cloud & DevOps",
    "GCP": "Cloud & DevOps",
    "Kubernetes": "Cloud & DevOps",
    "Docker": "Cloud & DevOps",
    "Apache Spark": "Data Engineering & Infra",
    "Hadoop": "Data Engineering & Infra",
    "Airflow": "Data Engineering & Infra",
    "Kafka": "Data Engineering & Infra",
    "CI/CD": "Cloud & DevOps",
    "DevOps": "Cloud & DevOps",
    "Linux / Unix": "Cloud & DevOps",

    # BI & Analytics Tools
    "Tableau": "BI & Analytics",
    "Power BI": "BI & Analytics",
    "Excel": "BI & Analytics",
    "Looker": "BI & Analytics",
    "Snowflake": "Data Engineering & Infra",
    "Databricks": "Data Engineering & Infra",

    # Software Engineering Practices
    "Agile": "Engineering Practices",
    "Git": "Engineering Practices",
    "Microservices": "Engineering Practices",
    "System design": "Engineering Practices",
    "REST APIs": "Engineering Practices",

    # Soft & Professional Skills
    "Communication": "Soft & Professional Skills",
    "Stakeholder management": "Soft & Professional Skills",
    "Leadership": "Soft & Professional Skills",
    "Collaboration": "Soft & Professional Skills",
    "Problem solving": "Soft & Professional Skills",
}

# canonical_skill -> list of surface forms/synonyms (case-insensitive)
DEFAULT_SKILL_SYNONYMS = {
    # Languages
    "Python": ["python", "py"],
    "SQL": ["sql", "postgresql", "mysql", "t-sql", "pl/sql", "bigquery sql", "snowflake sql", "sqlite"],
    "R": [r"\br\b"],
    "Java": [r"\bjava\b"],
    "JavaScript": ["javascript", r"\bjs\b"],
    "TypeScript": ["typescript", r"\bts\b"],
    "C++": ["c++", "c\\+\\+"],
    "C": [r"\bc\b"],
    "C#": ["c#", "c\\#", "c-sharp"],
    "Go": [r"\bgo\b", "golang"],
    "Rust": [r"\brust\b"],

    # AI / Machine Learning & Data Science
    "Machine learning": ["machine learning", r"\bml\b"],
    "Deep learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Computer vision": ["computer vision", r"\bcv\b"],
    "TensorFlow": ["tensorflow", "tf"],
    "PyTorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Statistics": ["statistics", "probability", "statistical modeling"],
    "LLM / RAG": ["llm", "large language model", "rag", "retrieval augmented", "langchain", "llamaindex", "generative ai", "genai"],

    # Cloud, Infra & DevOps
    "AWS": ["aws", "amazon web services", "amazon ec2", "amazon s3"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Docker": ["docker", "containerization", "containers"],
    "Apache Spark": ["spark", "pyspark", "apache spark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow", "apache airflow"],
    "Kafka": ["kafka", "apache kafka"],
    "CI/CD": ["ci/cd", "ci-cd", "continuous integration", "continuous deployment", "github actions", "jenkins", "gitlab ci"],
    "DevOps": ["devops", "site reliability engineering", "sre"],
    "Linux / Unix": ["linux", "unix", "ubuntu", "bash", "shell scripting"],

    # BI & Analytics Tools
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel", "microsoft excel", "spreadsheets"],
    "Looker": ["looker", "lookml"],
    "Snowflake": ["snowflake"],
    "Databricks": ["databricks"],

    # Software Engineering Practices
    "Agile": ["agile", "scrum", "kanban", "sprints"],
    "Git": ["git", "github", "gitlab", "version control"],
    "Microservices": ["microservices", "microservice", "service-oriented"],
    "System design": ["system design", "distributed systems", "scalable systems", "high-availability"],
    "REST APIs": ["rest api", "restful", "rest apis", "fastapi", "flask"],

    # Soft & Professional Skills
    "Communication": ["communication", "communicating", "written communication", "verbal communication"],
    "Stakeholder management": ["stakeholder", "stakeholders", "stakeholder management"],
    "Leadership": ["leadership", "mentoring", "mentor", "lead teams"],
    "Collaboration": ["collaboration", "collaborate", "teamwork", "cross-functional"],
    "Problem solving": ["problem solving", "problem-solving", "analytical thinking"],
}

# For backward compatibility with existing starter scripts
SKILL_SYNONYMS = copy.deepcopy(DEFAULT_SKILL_SYNONYMS)


def get_default_taxonomy():
    """Return a fresh copy of the default skill synonyms map."""
    return copy.deepcopy(DEFAULT_SKILL_SYNONYMS)


def get_category_for_skill(skill_name: str) -> str:
    """Return the category for a given skill or 'Other / Custom' if unknown."""
    return SKILL_CATEGORIES.get(skill_name, "Other / Custom")
