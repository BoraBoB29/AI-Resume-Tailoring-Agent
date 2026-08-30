from src.job_ingestion.models import Job


def normalize_job(data: dict) -> Job:
    if not isinstance(data, dict):
        raise TypeError("Job data must be a dictionary.")

    title = str(data.get("title", "")).strip()
    company = str(data.get("company", "")).strip()

    if not title:
        raise ValueError("Job title is required.")

    if not company:
        raise ValueError("Company name is required.")

    return Job(
        title=title,
        company=company,
        location=_clean_optional(data.get("location")),
        description=str(data.get("description", "")).strip(),
        url=_clean_optional(data.get("url")),
        source=_clean_optional(data.get("source")),
        job_id=_clean_optional(data.get("job_id")),
        employment_type=_clean_optional(data.get("employment_type")),
        workplace_type=_clean_optional(data.get("workplace_type")),
        salary=_clean_optional(data.get("salary")),
        requirements=_clean_list(data.get("requirements")),
        skills=_clean_list(data.get("skills")),
        raw_data=data,
    )


def _clean_optional(value):
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _clean_list(value):
    if not value:
        return []

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    return []