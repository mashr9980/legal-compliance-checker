import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:1.7b")

TEMP_DIR = BASE_DIR / "temp_files"
REPORTS_DIR = BASE_DIR / "reports"

TEMP_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf"}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_CONCURRENT_REQUESTS = 3

POLICY_ANALYSIS_CRITERIA = [
    {
        "id": "organizational_design",
        "name": "Organisational Design & Workforce Planning",
        "description": "Organization structure, workforce planning, job architecture, and reporting relationships",
        "keywords": ["organization", "structure", "workforce", "planning", "job", "architecture", "reporting", "hierarchy", "roles", "responsibilities", "manpower", "staffing"]
    },
    {
        "id": "talent_acquisition",
        "name": "Talent Acquisition",
        "description": "Employment categories, sourcing, selection, and onboarding processes",
        "keywords": ["recruitment", "hiring", "selection", "onboarding", "employment", "categories", "sourcing", "interview", "candidates", "joining"]
    },
    {
        "id": "learning_development",
        "name": "Learning & Development",
        "description": "Learning needs assessment, implementation, evaluation, and L&D programs",
        "keywords": ["training", "development", "learning", "education", "skills", "competency", "assessment", "program", "course", "capability"]
    },
    {
        "id": "performance_management",
        "name": "Performance Management",
        "description": "Performance variables, evaluation, rating, calibration, and performance-related processes",
        "keywords": ["performance", "evaluation", "appraisal", "rating", "kpi", "metrics", "objectives", "goals", "assessment", "feedback", "calibration"]
    },
    {
        "id": "talent_management",
        "name": "Talent Management",
        "description": "Succession planning, career progression, and talent development",
        "keywords": ["succession", "career", "progression", "advancement", "talent", "development", "promotion", "growth", "path", "pipeline"]
    },
    {
        "id": "compensation_benefits",
        "name": "Compensation & Benefits",
        "description": "Salary structure, processing, increases, allowances, benefits, and variable pay",
        "keywords": ["salary", "compensation", "benefits", "allowance", "pay", "wage", "bonus", "incentive", "reward", "variable", "increase"]
    },
    {
        "id": "hr_operations",
        "name": "Human Capital Operations",
        "description": "Employee relations, services, leave management, and separation processes",
        "keywords": ["employee", "relations", "services", "leave", "vacation", "separation", "termination", "resignation", "grievance", "disciplinary"]
    },
    {
        "id": "regulatory_compliance",
        "name": "Regulatory Compliance & Governance",
        "description": "MHRSD compliance, GOSI laws, anti-harassment, and Saudization requirements",
        "keywords": ["compliance", "regulatory", "mhrsd", "gosi", "harassment", "saudization", "nitaqat", "labor", "law", "governance"]
    },
    {
        "id": "policy_quality",
        "name": "Overall Policy Quality & Maturity",
        "description": "Policy structure, quality, version control, and organizational maturity",
        "keywords": ["policy", "quality", "maturity", "version", "control", "approval", "ownership", "documentation", "governance", "standard"]
    }
]

CHUNK_SIZE = 4000
OVERLAP_SIZE = 200
MAX_PROMPT_LENGTH = 8000
CONFIDENCE_THRESHOLD = 0.6