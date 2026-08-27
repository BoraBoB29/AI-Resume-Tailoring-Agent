import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual Mistral tailoring script; run directly when API access is intended.",
        allow_module_level=True,
    )

import yaml
from pathlib import Path
from dotenv import load_dotenv

from src.llm_tailor import ResumeTailor


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    ".env",
    override=True
)


# ============================================================
# PATHS
# ============================================================

MASTER_RESUME_PATH = Path(
    "data/master_resume.yaml"
)

JOB_DESCRIPTION_PATH = Path(
    "data/job_description.txt"
)


# ============================================================
# CHECK FILES
# ============================================================

if not MASTER_RESUME_PATH.exists():
    raise FileNotFoundError(
        f"Master resume not found: {MASTER_RESUME_PATH}"
    )

if not JOB_DESCRIPTION_PATH.exists():
    raise FileNotFoundError(
        f"Job description not found: {JOB_DESCRIPTION_PATH}"
    )


# ============================================================
# LOAD MASTER RESUME
# ============================================================

with open(
    MASTER_RESUME_PATH,
    "r",
    encoding="utf-8"
) as f:

    master_resume = yaml.safe_load(f)


# ============================================================
# LOAD JOB DESCRIPTION
# ============================================================

job_description = JOB_DESCRIPTION_PATH.read_text(
    encoding="utf-8"
)


# ============================================================
# INPUT CHECK
# ============================================================

print()
print("================================")
print("TAILORING INPUT")
print("================================")

print(
    "Master Resume:",
    MASTER_RESUME_PATH
)

print(
    "Job Description:",
    JOB_DESCRIPTION_PATH
)

print(
    "Name:",
    master_resume["contact"]["name"]
)

print(
    "Experience:",
    len(master_resume.get("experience", []))
)

print(
    "Projects:",
    len(master_resume.get("projects", []))
)

print(
    "Certifications:",
    len(master_resume.get("certifications", []))
)


# ============================================================
# CALL MISTRAL
# ============================================================

print()
print("================================")
print("CALLING MISTRAL")
print("================================")

tailor = ResumeTailor()

result = tailor.tailor(
    master_resume,
    job_description
)


# ============================================================
# SAVE OUTPUT
# ============================================================

output_path = Path(
    "output/tailored_resume.yaml"
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    yaml.safe_dump(
        result,
        f,
        sort_keys=False,
        allow_unicode=True
    )


# ============================================================
# RESULT
# ============================================================

print()
print("================================")
print("TAILORING SUCCESS")
print("================================")

print(
    "Output:",
    output_path
)

print(
    "Certifications:",
    len(
        result.get(
            "certifications",
            []
        )
    )
)

print(
    "Experience:",
    len(
        result.get(
            "experience",
            []
        )
    )
)

print(
    "Projects:",
    len(
        result.get(
            "projects",
            []
        )
    )
)

print(
    "Skill Categories:",
    len(
        result.get(
            "skills",
            {}
        )
    )
)