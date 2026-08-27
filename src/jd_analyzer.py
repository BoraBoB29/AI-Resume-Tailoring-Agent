"""Extract structured hiring requirements from a job description."""

import json
import os
import re
from typing import List, Optional

from dotenv import load_dotenv
from mistralai.client import Mistral

from src.schema import JDRequirement


load_dotenv()


EXTRACTION_PROMPT = """
Extract only hiring requirements explicitly supported by the job description.

Return JSON with exactly this shape:
{
  "requirements": [
    {
      "requirement": "SQL",
      "evidence_level": "required",
      "supporting_evidence": []
    }
  ]
}

Classify each requirement exactly once as:
- required: explicitly mandatory or required
- preferred: explicitly preferred, desired, or nice-to-have
- implicit: meaningful expectation stated without mandatory/preferred wording

Include skills, responsibilities, domains, tools/platforms, seniority or
experience, education, and other meaningful hiring requirements. Do not invent
requirements, candidate facts, or evidence. Prefer concise atomic phrases:
split independent tools, skills, and responsibilities rather than copying
sentences. For example, "Excel and PowerPoint" becomes two requirements and
"root causes and resolutions" becomes "Root cause analysis" and "Problem
resolution". Do not generate a resume.
""".strip()


def _deduplicate(requirements: List[JDRequirement]) -> List[JDRequirement]:
    seen = set()
    unique = []

    for requirement in requirements:
        key = (_canonical_requirement(requirement.requirement), requirement.evidence_level)
        if key in seen:
            continue
        seen.add(key)
        unique.append(requirement)

    return unique


def _canonical_requirement(text: str) -> str:
    """Normalize harmless wording variants for requirement deduplication."""
    value = re.sub(r"\s+", " ", text.strip().casefold())
    value = re.sub(r"^(knowledge|experience|proficiency|familiarity)\s+(of|with)\s+", "", value)
    value = re.sub(r"\s+(querying|queries)$", "", value)
    return value


def _split_list(value: str) -> List[str]:
    value = re.sub(r"\s+", " ", value.strip(" ."))
    parts = re.split(r"\s*,\s*|\s+and\s+|\s+or\s+", value, flags=re.IGNORECASE)
    return [
        re.sub(r"^(?:and|or)\s+", "", part, flags=re.IGNORECASE).strip(" .")
        for part in parts
        if part.strip(" .")
    ]


def _atomic_phrases(text: str) -> List[str]:
    """Reduce common sentence-like model phrases to JD-faithful atoms."""
    value = re.sub(r"\s+", " ", text.strip())
    lowered = value.casefold()

    if lowered.startswith("proficiency in "):
        return _split_list(value[len("proficiency in "):])

    including_match = re.match(
        r"^(.+?),\s*including\s+(.+)$",
        value,
        flags=re.IGNORECASE,
    )
    if including_match:
        return [including_match.group(1).strip()] + _split_list(including_match.group(2))

    match = re.match(
        r"^(?:basic )?knowledge of (.+?)\s+for\s+(.+)$",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        return _split_list(match.group(1)) + [match.group(2).strip(" .")]

    if re.search(r"metrics and reports", lowered):
        return ["Metrics reporting"]

    if "investigating" in lowered and "root causes" in lowered:
        return ["Issue investigation", "Root cause analysis", "Problem resolution"]

    if "investigating" in lowered and "issue" in lowered:
        return ["Issue investigation"]

    if "root causes" in lowered:
        phrases = ["Root cause analysis"]
        if "providing resolutions" in lowered or "providing resolution" in lowered:
            phrases.append("Problem resolution")
        return phrases

    if "providing resolutions" in lowered or "providing resolution" in lowered:
        return ["Problem resolution"]

    match = re.match(r"^experience creating (.+)$", value, flags=re.IGNORECASE)
    if match:
        return [
            re.sub(r"^dashboards$", "Dashboard development", part, flags=re.IGNORECASE)
            if part.casefold() == "dashboards"
            else re.sub(r"^kpis$", "KPI reporting", part, flags=re.IGNORECASE)
            if part.casefold() == "kpis"
            else re.sub(r"^automated reports$", "Automated reporting", part, flags=re.IGNORECASE)
            for part in _split_list(match.group(1))
        ]

    return [value]


def _atomicize(requirements: List[JDRequirement]) -> List[JDRequirement]:
    atomic = []
    for requirement in requirements:
        for phrase in _atomic_phrases(requirement.requirement):
            atomic.append(
                requirement.model_copy(
                    update={"requirement": phrase}
                )
            )
    return _deduplicate(atomic)


def _parse_response(content) -> List[JDRequirement]:
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Mistral returned an empty JD analysis response.")

    try:
        payload = json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("Mistral returned invalid JD analysis JSON.") from exc

    if isinstance(payload, dict):
        payload = payload.get("requirements")

    if not isinstance(payload, list):
        raise RuntimeError("JD analysis response must contain a requirements list.")

    try:
        requirements = [JDRequirement.model_validate(item) for item in payload]
    except Exception as exc:
        raise RuntimeError("JD analysis response contains invalid requirements.") from exc

    return _atomicize(requirements)


def extract_requirements(
    job_description: str,
    client=None,
    model: Optional[str] = None,
) -> List[JDRequirement]:
    """Extract validated requirements using the configured Mistral model."""
    if not isinstance(job_description, str) or not job_description.strip():
        return []

    if len(job_description.strip()) < 10:
        return []

    if client is None:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. Check your .env file."
            )
        client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model=model or os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": job_description},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise RuntimeError("Mistral returned an unusable JD analysis response.") from exc

    return _parse_response(content)


def print_analysis(requirements: List[JDRequirement]) -> None:
    """Print a concise grouped representation for normal CLI debugging."""
    print("========== JD ANALYSIS ==========")
    for level in ("required", "preferred", "implicit"):
        print(f"{level.title()}:")
        for requirement in requirements:
            if requirement.evidence_level == level:
                print(f"- {requirement.requirement}")
    print("=================================")