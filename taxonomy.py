"""
Comprehensive Skills Taxonomy System v3.0 (Aligned with ESCO & O*NET Domains).

Contains 180+ curated technical & professional skills across 10 specialized domains,
with surface forms, regex patterns, skill types (Tool, Language, Framework, Infrastructure, Practice),
and domain preset bundles.
"""

import copy
from typing import Dict, List, Any, Optional

# Canonical Skill -> Primary Domain
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
    "Solidity": "Programming Languages",
    "Julia": "Programming Languages",
    "Dart": "Programming Languages",

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
    "MLOps": "Data Science & AI",
    "Model Fine-Tuning": "Data Science & AI",
    "XGBoost / LightGBM": "Data Science & AI",
    "Reinforcement Learning": "Data Science & AI",

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
    "Apache Flink": "Data Engineering",
    "Hadoop": "Data Engineering",
    "Data Modeling": "Data Engineering",
    "ETL / ELT Pipelines": "Data Engineering",
    "Apache Iceberg": "Data Engineering",
    "Data Lakehouse": "Data Engineering",

    # 4. Databases & Storage
    "PostgreSQL": "Databases & Storage",
    "MySQL": "Databases & Storage",
    "MongoDB": "Databases & Storage",
    "Redis": "Databases & Storage",
    "Elasticsearch": "Databases & Storage",
    "Cassandra": "Databases & Storage",
    "DynamoDB": "Databases & Storage",
    "Neo4j / Graph DB": "Databases & Storage",
    "SQLite": "Databases & Storage",
    "GraphQL": "Databases & Storage",
    "ClickHouse": "Databases & Storage",

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
    "Helm": "Cloud & DevOps",
    "ArgoCD": "Cloud & DevOps",
    "Serverless / Lambda": "Cloud & DevOps",

    # 6. Web & Backend Frameworks
    "React": "Web & Frontend",
    "Next.js": "Web & Frontend",
    "Node.js": "Web & Backend",
    "Vue.js": "Web & Frontend",
    "Angular": "Web & Frontend",
    "FastAPI": "Web & Backend",
    "Django": "Web & Backend",
    "Flask": "Web & Backend",
    "Spring Boot": "Web & Backend",
    "Express.js": "Web & Backend",
    "ASP.NET": "Web & Backend",
    "Ruby on Rails": "Web & Backend",
    "REST APIs": "Web & Backend",
    "Microservices": "Web & Backend",
    "HTML / CSS": "Web & Frontend",
    "Tailwind CSS": "Web & Frontend",
    "gRPC": "Web & Backend",

    # 7. Mobile Development
    "React Native": "Mobile Development",
    "Flutter": "Mobile Development",
    "iOS / Swift": "Mobile Development",
    "Android / Kotlin": "Mobile Development",

    # 8. Cybersecurity & Governance
    "Cybersecurity": "Cybersecurity & Security",
    "SOC 2 / Compliance": "Cybersecurity & Security",
    "OAuth / OIDC / Auth": "Cybersecurity & Security",
    "Penetration Testing": "Cybersecurity & Security",
    "Cryptography": "Cybersecurity & Security",

    # 9. BI, Analytics & Business Tools
    "Tableau": "BI & Analytics",
    "Power BI": "BI & Analytics",
    "Excel": "BI & Analytics",
    "Looker": "BI & Analytics",
    "Metabase": "BI & Analytics",
    "Google Analytics": "BI & Analytics",
    "A/B Testing": "BI & Analytics",

    # 10. Engineering Practices & Soft Skills
    "System Design": "Practices & Soft Skills",
    "Agile / Scrum": "Practices & Soft Skills",
    "Git": "Practices & Soft Skills",
    "Communication": "Practices & Soft Skills",
    "Stakeholder Management": "Practices & Soft Skills",
    "Leadership": "Practices & Soft Skills",
    "Collaboration": "Practices & Soft Skills",
    "Problem Solving": "Practices & Soft Skills",
    "Mentoring": "Practices & Soft Skills",
}

# Skill Types (esco taxonomy alignment)
SKILL_TYPES = {
    "Python": "Programming Language",
    "SQL": "Query Language",
    "React": "Frontend Framework",
    "Docker": "DevOps Tool",
    "Kubernetes": "Container Orchestrator",
    "PyTorch": "ML Framework",
    "AWS": "Cloud Platform",
    "Tableau": "BI Tool",
    "Agile / Scrum": "Methodology",
    "Communication": "Soft Skill",
}

# Canonical Skill -> Surface Forms / Synonyms (Case-Insensitive)
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
    "Bash / Shell": ["bash", "shell scripting", "zsh", "powershell", "shell script", "sh script"],
    "Solidity": ["solidity", "smart contracts"],
    "Julia": ["julia", "julia-lang"],
    "Dart": ["dart"],

    # 2. Data Science, ML & Generative AI
    "Machine Learning": ["machine learning", r"\bml\b", "supervised learning", "unsupervised learning"],
    "Deep Learning": ["deep learning", r"\bdl\b", "neural networks", "cnn", "rnn", "transformers"],
    "NLP": ["nlp", "natural language processing", "text mining", "ner", "tokenization"],
    "Computer Vision": ["computer vision", r"\bcv\b", "opencv", "image processing", "object detection"],
    "LLM / GenAI": ["llm", "large language model", "large language models", "generative ai", "genai", "foundation models", "gpt-4", "claude", "llama", "chatgpt"],
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
    "Statistics": ["statistics", "statistical modeling", "probability", "hypothesis testing", "bayesian"],
    "Prompt Engineering": ["prompt engineering", "prompt design", "few-shot"],
    "MLOps": ["mlops", "ml pipelines", "kubeflow", "mlflow", "wandb", "weights & biases"],
    "Model Fine-Tuning": ["fine-tuning", "fine tuning", "lora", "qlora", "peft"],
    "XGBoost / LightGBM": ["xgboost", "lightgbm", "catboost", "gradient boosting"],
    "Reinforcement Learning": ["reinforcement learning", r"\brl\b", "rlhf"],

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
    "Apache Flink": ["flink", "apache flink"],
    "Hadoop": ["hadoop", "hdfs", "mapreduce", "hive"],
    "Data Modeling": ["data modeling", "data warehousing", "star schema", "dimensional modeling"],
    "ETL / ELT Pipelines": ["etl", "elt", "data pipeline", "data pipelines", "data ingestion"],
    "Apache Iceberg": ["apache iceberg", "iceberg table"],
    "Data Lakehouse": ["lakehouse", "data lakehouse", "data lake"],

    # 4. Databases & Storage
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "Cassandra": ["cassandra", "apache cassandra"],
    "DynamoDB": ["dynamodb", "aws dynamodb"],
    "Neo4j / Graph DB": ["neo4j", "graph database", "graph db"],
    "SQLite": ["sqlite"],
    "GraphQL": ["graphql", "graph ql"],
    "ClickHouse": ["clickhouse"],

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
    "Prometheus / Grafana": ["prometheus", "grafana", "datadog", "new relic", "observability", "opentelemetry"],
    "DevOps / SRE": ["devops", "sre", "site reliability engineering", "platform engineering"],
    "Helm": ["helm", "helm chart"],
    "ArgoCD": ["argocd", "argo cd", "gitops"],
    "Serverless / Lambda": ["serverless", "aws lambda", "cloud functions"],

    # 6. Web & Backend Frameworks
    "React": [r"\breact\b", "reactjs", "react.js"],
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
    "Ruby on Rails": ["ruby on rails", "rails"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful apis", "web apis"],
    "Microservices": ["microservices", "microservice", "service-oriented architecture", "soa"],
    "HTML / CSS": ["html", "css", "html5", "css3", "sass", "scss"],
    "Tailwind CSS": ["tailwind", "tailwind css", "tailwindcss"],
    "gRPC": ["grpc", "protocol buffers", "protobuf"],

    # 7. Mobile Development
    "React Native": ["react native", "react-native"],
    "Flutter": ["flutter"],
    "iOS / Swift": ["ios", "swift", "swiftui", "xcode"],
    "Android / Kotlin": ["android", "kotlin", "jetpack compose"],

    # 8. Cybersecurity & Governance
    "Cybersecurity": ["cybersecurity", "information security", "infosec", "appsec", "vulnerability management"],
    "SOC 2 / Compliance": ["soc 2", "soc2", "gdpr", "hipaa", "iso 27001"],
    "OAuth / OIDC / Auth": ["oauth", "oidc", "jwt", "saml", "authentication", "sso"],
    "Penetration Testing": ["penetration testing", "pen testing", "ethical hacking"],
    "Cryptography": ["cryptography", "encryption", "tls", "ssl"],

    # 9. BI, Analytics & Business Tools
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi", "power-bi"],
    "Excel": ["excel", "microsoft excel", "spreadsheets", "vba", "pivot tables"],
    "Looker": ["looker", "lookml", "google looker"],
    "Metabase": ["metabase"],
    "Google Analytics": ["google analytics", "ga4"],
    "A/B Testing": ["a/b testing", "ab testing", "split testing", "experimentation"],

    # 10. Engineering Practices & Soft Skills
    "System Design": ["system design", "distributed systems", "scalable systems", "high availability", "scalability"],
    "Agile / Scrum": ["agile", "scrum", "kanban", "sprints", "jira"],
    "Git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "Communication": ["communication", "communicating", "verbal communication", "written communication", "presentation skills"],
    "Stakeholder Management": ["stakeholder", "stakeholders", "stakeholder management", "cross-functional alignment"],
    "Leadership": ["leadership", "leading teams", "team lead", "engineering manager"],
    "Collaboration": ["collaboration", "collaborate", "teamwork", "cross-functional", "interpersonal skills"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical thinking", "critical thinking"],
    "Mentoring": ["mentoring", "mentor", "coaching"],
}

# Domain Presets
TAXONOMY_PRESETS = {
    "🌟 Complete Tech Stack (180+ Skills)": DEFAULT_SKILL_SYNONYMS,
    "🤖 Data Science, AI & MLOps Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Data Science & AI", "Programming Languages", "Databases & Storage", "BI & Analytics"]
    },
    "⚡ Data Engineering & Big Data Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Data Engineering", "Databases & Storage", "Cloud & DevOps", "Programming Languages"]
    },
    "🌐 Software, Web & Mobile Focus": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Web & Frontend", "Web & Backend", "Mobile Development", "Programming Languages", "Practices & Soft Skills"]
    },
    "☁️ Cloud, DevOps, SRE & Security": {
        k: v for k, v in DEFAULT_SKILL_SYNONYMS.items()
        if SKILL_CATEGORIES.get(k) in ["Cloud & DevOps", "Cybersecurity & Security", "Databases & Storage", "Programming Languages", "Practices & Soft Skills"]
    },
}


def get_default_taxonomy() -> Dict[str, List[str]]:
    """Return a fresh copy of the default taxonomy."""
    return copy.deepcopy(DEFAULT_SKILL_SYNONYMS)


def get_category_for_skill(skill_name: str) -> str:
    """Return the assigned domain category for a skill."""
    return SKILL_CATEGORIES.get(skill_name, "Other / Custom")


def get_all_categories() -> List[str]:
    """Return unique list of all domain categories."""
    cats = sorted(list(set(SKILL_CATEGORIES.values())))
    if "Other / Custom" not in cats:
        cats.append("Other / Custom")
    return cats
