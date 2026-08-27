from typing import List, Dict, Optional, Any, Literal

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# CONTACT
# ============================================================

class Contact(BaseModel):

    model_config = ConfigDict(extra="ignore")

    name: str
    email: str
    phone: str
    location: str

    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


# ============================================================
# SKILLS
# ============================================================

class Skills(BaseModel):

    model_config = ConfigDict(extra="ignore")

    categories: Dict[str, List[str]] = Field(
        default_factory=dict
    )

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *args,
        **kwargs
    ):

        if isinstance(obj, dict):

            # Mistral may return:
            #
            # {
            #     "Data Analytics": [...],
            #     "Product Management": [...]
            # }
            #
            # Convert into:
            #
            # {
            #     "categories": {
            #         "Data Analytics": [...],
            #         "Product Management": [...]
            #     }
            # }

            if "categories" not in obj:

                obj = {
                    "categories": obj
                }

        return super().model_validate(
            obj,
            *args,
            **kwargs
        )


# ============================================================
# EXPERIENCE
# ============================================================

class Experience(BaseModel):

    model_config = ConfigDict(extra="ignore")

    company: str
    title: str
    location: str

    start_date: str
    end_date: str

    bullets: List[str] = Field(
        default_factory=list
    )


# ============================================================
# PROJECT
# ============================================================

class Project(BaseModel):

    model_config = ConfigDict(extra="ignore")

    name: str

    bullets: List[str] = Field(
        default_factory=list
    )

    tech_stack: List[str] = Field(
        default_factory=list
    )

    description: Optional[str] = None

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *args,
        **kwargs
    ):

        if isinstance(obj, dict):

            obj = dict(obj)

            # If the LLM returns a description instead
            # of bullets, convert it to one bullet.

            if (
                not obj.get("bullets")
                and obj.get("description")
            ):

                obj["bullets"] = [
                    obj["description"]
                ]

        return super().model_validate(
            obj,
            *args,
            **kwargs
        )


# ============================================================
# EDUCATION
# ============================================================

class Education(BaseModel):

    model_config = ConfigDict(extra="ignore")

    institution: str

    degree: str

    location: str

    start_date: str

    end_date: str

    gpa: Optional[str] = None

    details: List[str] = Field(
        default_factory=list
    )


# ============================================================
# CERTIFICATION
# ============================================================

class Certification(BaseModel):

    model_config = ConfigDict(extra="ignore")

    name: str

    issuer: str = ""

    category: str = ""

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *args,
        **kwargs
    ):

        # Prevent this error:
        #
        # Input should be a valid dictionary
        #
        # Mistral sometimes returns:
        #
        # "Google Data Analytics Professional Certificate
        #  (Google / Coursera)"
        #
        # instead of an object.

        if isinstance(obj, str):

            value = obj.strip()

            if "(" in value and ")" in value:

                name = value.split("(")[0].strip()

                issuer = (
                    value[
                        value.find("(") + 1:
                        value.rfind(")")
                    ]
                    .strip()
                )

            else:

                name = value
                issuer = ""

            obj = {
                "name": name,
                "issuer": issuer,
                "category": ""
            }

        return super().model_validate(
            obj,
            *args,
            **kwargs
        )


# ============================================================
# TAILORED RESUME
# ============================================================

class TailoredResume(BaseModel):

    model_config = ConfigDict(extra="ignore")

    contact: Contact

    summary: str

    skills: Skills

    experience: List[Experience]

    projects: List[Project]

    education: List[Education]

    certifications: List[Certification] = Field(
        default_factory=list
    )

    jd_analysis: Optional[Dict] = None

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *args,
        **kwargs
    ):

        if isinstance(obj, dict):

            obj = dict(obj)

            # Some LLM responses wrap everything in:
            #
            # {
            #     "tailored_resume": {
            #         ...
            #     }
            # }
            #
            # Automatically unwrap it.

            if "tailored_resume" in obj:

                nested = obj.get(
                    "tailored_resume"
                )

                if isinstance(nested, dict):

                    obj = nested

        return super().model_validate(
            obj,
            *args,
            **kwargs
        )


# ============================================================
# JD REQUIREMENT
# ============================================================

class JDRequirement(BaseModel):

    model_config = ConfigDict(extra="ignore")

    requirement: str

    evidence_level: Literal[
        "required",
        "preferred",
        "implicit"
    ]

    supporting_evidence: List[str] = Field(
        default_factory=list
    )


TailoredContent = TailoredResume