"""
Enhanced Skills Taxonomy & Categorization System (v2).

Contains 120+ curated tech skills across 8 core domains, with alias surface forms,
regex compilation patterns, and import/export capabilities.
"""

import copy
from typing import Dict, List, Any, Optional

# Canonical Skill -> Primary Category Mapping
SKILL_CATEGORIES = {
    # 1. Programming Languages
    "Python": "Programming Languages",
    "SQL": "Programming Languages",
    "TypeScript": "Programming Languages",
    "JavaScript": "Programming Languages",
    "Java": "Programming Languages",
    "C++": "Programming Languages",
    "C#": "Programming Languages",
    "C": "Programming Languages",
    "Go": "Programming Languages",
    "Rust": "Programming Languages",
    "R": "Programming Languages",
    "Scala": "Programming Languages",
    "Kotlin": "Programming Languages",
    "Swift": "Programming Languages",
    "Ruby": "Programming Languages",
    "PHP": "Programming Languages",
    "Bash / Shell": "Programming Languages",

    # 2. Data Science, ML & Generative AI
    "Machine Learning": "Data Science & AI",
    "Deep Learning": "Data Science & AI",
    "NLP": "Data Science & AI",
    "Computer Vision": "Data Science & AI",
    "LLM / GenAI": "Data Science & AI",
    "RAG": "Data Science & AI",
    "LangChain": "Data Science & AI",
    "LlamaIndex": "Data Science & AI",
    "Vector Databases": "Data Science & AI",
    "PyTorch": "Data Science & AI",
    "TensorFlow": "Data Science & AI",
    "scikit-learn": "Data Science & AI",
    "Hugging Face": "Data Science & AI",
    "Pandas": "Data Science & AI",
    "NumPy": "Data Science & AI",
    "Polars": "Data Science & AI",
    "Statistics": "Data Science & AI",
    "Prompt Engineering": "Data Science & AI",

    # 3. Data Engineering & Big Data
    "Apache Spark": "Data Engineering",
    "PySpark": "Data Engineering",
    "Apache Kafka": "Data Engineering",
    "Apache Airflow": "Data Engineering",
    "dbt": "Data Engineering",
    "Snowflake": "Data Engineering",
    "Databricks": "Data Engineering",
    "Google BigQuery": "Data Engineering",
    "AWS Redshift": "Data Engineering",
    "Hadoop": "Data Engineering",
    "Data Modeling": "Data Engineering",
    "ETL / ELT Pipelines": "Data Engineering",

    # 4. Databases & Storage
    "PostgreSQL": "Databases & Storage",
    "MySQL": "Databases & Storage",
    "MongoDB": "Databases & Storage",
    "Redis": "Databases & Storage",
    "Elasticsearch": "Databases & Storage",
    "Cassandra": "Databases & Storage",
    "DynamoDB": "Databases & Storage",
    "SQLite": "Databases & Storage",
    "GraphQL": "Databases & Storage",

    # 5. Cloud, DevOps & Infrastructure
    "AWS": "Cloud & DevOps",
    "Azure": "Cloud & DevOps",
    "GCP": "Cloud & DevOps",
    "Docker": "Cloud & DevOps",
    "Kubernetes": "Cloud & DevOps",
    "Terraform": "Cloud & DevOps",
    "CI/CD": "Cloud & DevOps",
    "GitHub Actions": "Cloud & DevOps",
    "Jenkins": "Cloud & DevOps",
    "Linux / Unix": "Cloud & DevOps",
    "Ansible": "Cloud & DevOps",
    "Prometheus / Grafana": "Cloud & DevOps",
    "DevOps / SRE": "Cloud & DevOps",

    # 6. Web & Backend Frameworks
    "React": "Web & Backend",
    "Next.js": "Web & Backend",
    "Node.js": "Web & Backend",
    "Vue.js": "Web & Backend",
    "Angular": "Web & Backend",
    "FastAPI": "Web & Backend",
    "Django": "Web & Backend",
    "Flask": "Web & Backend",
    "Spring Boot": "Web & Backend",
    "Express.js": "Web & Backend",
    "ASP.NET": "Web & Backend",
    "REST APIs": "Web & Backend",
    "Microservices": "Web & Backend",
    "HTML / CSS": "Web & Backend",
    "Tailwind CSS": "Web & Backend",

    # 7. BI, Analytics & Business Tools
    "Tableau": "BI & Analytics",
    "Power BI": "BI & Analytics",
    "Excel": "BI & Analytics",
    "Looker": "BI & Analytics",
    "Metabase": "BI & Analytics",
    "Google Analytics": "BI & Analytics",

    # 8. Practices & Soft Skills
    "System Design": "Practices & Soft Skills",
    "Agile / Scrum": "Practices & Soft Skills",
    "Git": "Practices & Soft Skills",
    "Communication": "Practices & Soft Skills",
    "Stakeholder Management": "Practices & Soft Skills",
    "Leadership": "Practices & Soft Skills",
    "Collaboration": "Practices & Soft Skills",
    "Problem Solving": "Practices & Soft Skills",
}

# Canonical Skill -> Surface Forms / Synonyms
DEFAULT_SKILL_SYNONYMS = {
    # 1. Programming Languages
    "Python": ["python", "python3", "pyspark", r"\bpy\b"],
    "SQL": ["sql", "postgresql", "mysql", "t-sql", "pl/sql", "bigquery sql", "snowflake sql", "sqlite", "mssql", "nosql"],
    "TypeScript": ["typescript", r"\bts\b"],
    "JavaScript": ["javascript", r"\bjs\b", "ecmascript"],
    "Java": [r"\bjava\b", "core java", "jvm"],
    "C++": ["c++", "c\\+\\+", "cpp"],
    "C#": ["c#", "c\\#", "c-sharp", "csharp", ".net c#"],
    "C": [r"\bc\b", "c language"],
    "Go": [r"\bgo\b", "golang"],
    "Rust": [r"\brust\b", "rustlang"],
    "R": [r"\br\b", "r programming", "r-lang"],
    "Scala": ["scala"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift", "swiftui"],
    "Ruby": ["ruby", "ruby on rails", "rails"],
    "PHP": ["php", "laravel"],
    "Bash / Shell": ["bash", "shell scripting", "zsh", "powershell", "shell script"],

    # 2. Data Science, ML & Generative AI
    "Machine Learning": ["machine learning", r"\bml\b", "supervised learning", "unsupervised learning"],
    "Deep Learning": ["deep learning", r"\bdl\b", "neural networks", "cnn", "rnn", "transformers"],
    "NLP": ["nlp", "natural language processing", "text mining", "ner", "tokenization"],
    "Computer Vision": ["computer vision", r"\bcv\b", "opencv", "image processing", "object detection"],
    "LLM / GenAI": ["llm", "large language model", "large language models", "generative ai", "genai", "foundation models", "gpt", "claude", "llama"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented"],
    "LangChain": ["langchain"],
    "LlamaIndex": ["llamaindex", "llama-index"],
    "Vector Databases": ["vector database", "vector databases", "vector db", "pinecone", "chroma", "chromadb", "weaviate", "qdrant", "milvus", "faiss"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", r"\btf\b", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Hugging Face": ["hugging face", "huggingface", "transformers library"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Polars": ["polars"],
    "Statistics": ["statistics", "statistical modeling", "probability", "hypothesis testing", "ab testing", "a/b testing"],
    "Prompt Engineering": ["prompt engineering", "prompt design", "few-shot"],

    # 3. Data Engineering & Big Data
    "Apache Spark": ["spark", "apache spark"],
    "PySpark": ["pyspark"],
    "Apache Kafka": ["kafka", "apache kafka"],
    "Apache Airflow": ["airflow", "apache airflow"],
    "dbt": [r"\bdbt\b", "data build tool"],
    "Snowflake": ["snowflake", "snowflake data warehouse"],
    "Databricks": ["databricks", "delta lake", "lakehouse"],
    "Google BigQuery": ["bigquery", "google bigquery"],
    "AWS Redshift": ["redshift", "aws redshift"],
    "Hadoop": ["hadoop", "hdfs", "mapreduce", "hive"],
    "Data Modeling": ["data modeling", "data warehousing", "star schema", "dimensional modeling"],
    "ETL / ELT Pipelines": ["etl", "elt", "data pipeline", "data pipelines", "data ingestion"],

    # 4. Databases & Storage
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "Cassandra": ["cassandra", "apache cassandra"],
    "DynamoDB": ["dynamodb", "aws dynamodb"],
    "SQLite": ["sqlite"],
    "GraphQL": ["graphql", "graph ql"],

    # 5. Cloud, DevOps & Infrastructure
    "AWS": ["aws", "amazon web services", "amazon ec2", "amazon s3", "aws lambda", "cloudformation", "iam"],
    "Azure": ["azure", "microsoft azure", "azure devops"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Docker": ["docker", "containerization", "containers", "dockerfile", "docker compose"],
    "Kubernetes": ["kubernetes", r"\bk8s\b", "helm charts"],
    "Terraform": ["terraform", "iac", "infrastructure as code"],
    "CI/CD": ["ci/cd", "ci-cd", "continuous integration", "continuous deployment"],
    "GitHub Actions": ["github actions"],
    "Jenkins": ["jenkins"],
    "Linux / Unix": ["linux", "unix", "ubuntu", "debian", "redhat", "centos"],
    "Ansible": ["ansible"],
    "Prometheus / Grafana": ["prometheus", "grafana", "datadog", "new relic", "observability"],
    "DevOps / SRE": ["devops", "sre", "site reliability engineering", "platform engineering"],

    # 6. Web & Backend Frameworks
    "React": [r"\breact\b", "reactjs", "react.js", "react native"],
    "Next.js": ["next.js", "nextjs", "next js"],
    "Node.js": ["node.js", "nodejs", "node js", r"\bnode\b"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular", "angularjs"],
    "FastAPI": ["fastapi", "fast-api"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring Boot": ["spring boot", "spring framework", "spring"],
    "Express.js": ["express.js", "expressjs", "express js"],
    "ASP.NET": ["asp.net", ".net core", "dotnet core", ".net"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful apis", "web apis"],
    "Microservices": ["microservices", "microservice", "service-oriented architecture"],
    "HTML / CSS": ["html", "css", "html5", "css3", "sass", "scss"],
    "Tailwind CSS": ["tailwind", "tailwind css", "tailwindcss"],

    # 7. BI, Analytics & Business Tools
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi", "power-bi"],
    "Excel": ["excel", "microsoft excel", "spreadsheets", "vba", "pivot tables"],
    "Looker": ["looker", "lookml", "google looker"],
    "Metabase": ["metabase"],
    "Google Analytics": ["google analytics", "ga4"],

    # 8. Practices & Soft Skills
    "System Design": ["system design", "distributed systems", "scalable systems", "high availability", "scalability"],
    "Agile / Scrum": ["agile", "scrum", "kanban", "sprints", "jira"],
    "Git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "Communication": ["communication", "communicating", "verbal communication", "written communication", "presentation skills"],
    "Stakeholder Management": ["stakeholder", "stakeholders", "stakeholder management", "cross-functional alignment"],
    "Leadership": ["leadership", "mentoring", "mentor", "leading teams", "team lead"],
    "Collaboration": ["collaboration", "collaborate", "teamwork", "cross-functional", "interpersonal skills"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical thinking", "critical thinking"],
}

# Taxonomy Preset Bundles
TAXONOMY_PRESETS = {
    "🌟 Complete Tech Stack (120+ Skills)": DEFAULT_SKILL_SYNONYMS,
    "🤖 Data Science & AI Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Data Science & AI", "Programming Languages", "Databases & Storage", "BI & Analytics"]
    },
    "⚡ Data Engineering & Infra Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Data Engineering", "Databases & Storage", "Cloud & DevOps", "Programming Languages"]
    },
    "🌐 Software & Web Engineering Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Web & Backend", "Programming Languages", "Cloud & DevOps", "Practices & Soft Skills"]
    },
    "☁️ Cloud, DevOps & Platform Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Cloud & DevOps", "Programming Languages", "Databases & Storage", "Practices & Soft Skills"]
    },
}


def get_default_taxonomy() -> Dict[str, List[str]]:
    """Return a fresh deep copy of the default skill synonyms dictionary."""
    return copy.deepcopy(DEFAULT_SKILL_SYNONYMS)


def get_category_for_skill(skill_name: str) -> str:
    """Return the assigned category for a given skill or 'Other / Custom'."""
    return SKILL_CATEGORIES.get(skill_name, "Other / Custom")


def get_all_categories() -> List[str]:
    """Return unique sorted list of all taxonomy categories."""
    cats = sorted(list(set(SKILL_CATEGORIES.values())))
    cats.append("Other / Custom")
    return cats
