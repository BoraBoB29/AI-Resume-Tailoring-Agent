"""Extract structured hiring requirements from a job description."""

import json
import os
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
requirements, candidate facts, or evidence. Do not generate a resume.
""".strip()


def _deduplicate(requirements: List[JDRequirement]) -> List[JDRequirement]:
    seen = set()
    unique = []

    for requirement in requirements:
        key = (requirement.requirement.strip().casefold(), requirement.evidence_level)
        if key in seen:
            continue
        seen.add(key)
        unique.append(requirement)

    return unique


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

    return _deduplicate(requirements)


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