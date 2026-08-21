import json
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from src.schema import TailoredResume


load_dotenv()


class ResumeTailor:

    def __init__(self):

        api_key = os.getenv("MISTRAL_API_KEY")

        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. "
                "Check your .env file."
            )

        self.model = os.getenv(
            "MISTRAL_MODEL",
            "mistral-large-latest"
        )

        self.client = Mistral(
            api_key=api_key
        )

    # ========================================================
    # FALLBACK SKILLS
    # ========================================================

    def _fallback_skills(self, master_resume):

        source_skills = master_resume.get(
            "skills",
            {}
        )

        if not isinstance(source_skills, dict):
            return {}

        if "categories" in source_skills:

            categories = source_skills.get(
                "categories",
                {}
            )

            if isinstance(categories, dict):
                return categories

        return source_skills

    # ========================================================
    # CANONICAL PROJECTS
    # ========================================================

    def _get_canonical_projects(
        self,
        master_resume
    ):

        projects = master_resume.get(
            "projects",
            []
        )

        if not isinstance(projects, list):
            return []

        return [
            project
            for project in projects
            if isinstance(project, dict)
        ]

    # ========================================================
    # PROJECT LOOKUP
    # ========================================================

    def _project_lookup(
        self,
        master_resume
    ):

        lookup = {}

        for project in self._get_canonical_projects(
            master_resume
        ):

            name = str(
                project.get(
                    "name",
                    ""
                )
            ).strip()

            if name:
                lookup[
                    name.lower()
                ] = project

        return lookup

    # ========================================================
    # CONTACT NORMALIZATION
    # ========================================================

    def _normalize_contact(
        self,
        data,
        master_resume
    ):

        contact = data.get(
            "contact",
            {}
        )

        if not isinstance(
            contact,
            dict
        ):
            contact = {}

        master_contact = master_resume.get(
            "contact",
            {}
        )

        if not isinstance(
            master_contact,
            dict
        ):
            master_contact = {}

        # Preserve canonical values
        for field in [
            "name",
            "email",
            "phone",
            "linkedin",
            "github",
            "portfolio"
        ]:

            if not contact.get(field):

                if master_contact.get(field):

                    contact[field] = (
                        master_contact[field]
                    )

        # ALWAYS preserve full location
        master_location = str(
            master_contact.get(
                "location",
                ""
            )
        ).strip()

        if master_location:
            contact["location"] = master_location

        location = str(
            contact.get(
                "location",
                ""
            )
        ).strip()

        if location.lower() in {
            "",
            "india",
            ", india",
            "india,"
        }:

            location = "Pune, India"

        contact["location"] = location

        data["contact"] = contact

        return data

    # ========================================================
    # EDUCATION NORMALIZATION
    # ========================================================

    def _normalize_education(
        self,
        data,
        master_resume
    ):

        education = data.get(
            "education"
        )

        if isinstance(
            education,
            dict
        ):

            education = [
                education
            ]

        elif not isinstance(
            education,
            list
        ):

            education = []

        master_education = master_resume.get(
            "education",
            []
        )

        if not isinstance(
            master_education,
            list
        ):
            master_education = []

        # Preserve missing canonical education
        # from master resume.
        if len(education) < len(
            master_education
        ):

            existing = {
                str(
                    item.get(
                        "institution",
                        ""
                    )
                ).strip().lower()
                for item in education
                if isinstance(item, dict)
            }

            for master_item in master_education:

                if not isinstance(
                    master_item,
                    dict
                ):
                    continue

                institution = str(
                    master_item.get(
                        "institution",
                        ""
                    )
                ).strip()

                if (
                    institution
                    and institution.lower()
                    not in existing
                ):

                    education.append(
                        dict(master_item)
                    )

        # Preserve canonical GPA / percentages
        for item in education:

            if not isinstance(
                item,
                dict
            ):
                continue

            institution = str(
                item.get(
                    "institution",
                    ""
                )
            ).lower()

            for master_item in master_education:

                if not isinstance(
                    master_item,
                    dict
                ):
                    continue

                master_institution = str(
                    master_item.get(
                        "institution",
                        ""
                    )
                ).lower()

                if (
                    institution
                    and institution
                    == master_institution
                ):

                    # Preserve GPA
                    if master_item.get(
                        "gpa"
                    ):

                        item["gpa"] = (
                            master_item["gpa"]
                        )

                    # Preserve details
                    if master_item.get(
                        "details"
                    ):

                        item["details"] = (
                            master_item["details"]
                        )

        data["education"] = education

        return data

    # ========================================================
    # SKILLS NORMALIZATION
    # ========================================================

    def _normalize_skills(
        self,
        data,
        master_resume
    ):

        skills = data.get(
            "skills"
        )

        if not skills:

            data["skills"] = {
                "categories":
                    self._fallback_skills(
                        master_resume
                    )
            }

            return data

        if isinstance(
            skills,
            dict
        ):

            if "categories" not in skills:

                skills = {
                    "categories": skills
                }

            data["skills"] = skills

            return data

        data["skills"] = {
            "categories":
                self._fallback_skills(
                    master_resume
                )
        }

        return data

    # ========================================================
    # EXPERIENCE NORMALIZATION
    # ========================================================

    def _normalize_experience(
        self,
        data
    ):

        experience = data.get(
            "experience",
            []
        )

        if not isinstance(
            experience,
            list
        ):

            data["experience"] = []

            return data

        for exp in experience:

            if not isinstance(
                exp,
                dict
            ):
                continue

            bullets = exp.get(
                "bullets",
                []
            )

            if isinstance(
                bullets,
                str
            ):

                bullets = [
                    bullets
                ]

            exp["bullets"] = [
                str(
                    bullet
                ).strip()
                for bullet in bullets
                if str(
                    bullet
                ).strip()
            ]

        data["experience"] = experience

        return data

    # ========================================================
    # EXPERIENCE CONTENT FLOOR
    # ========================================================

    def _ensure_experience_content_floor(
        self,
        result,
        master_resume
    ):

        master_experience = master_resume.get(
            "experience",
            []
        )

        if not isinstance(
            master_experience,
            list
        ):
            return result

        result_experience = result.get(
            "experience",
            []
        )

        if not isinstance(
            result_experience,
            list
        ):
            result_experience = []

        # ----------------------------------------------------
        # Build master experience lookup
        # ----------------------------------------------------

        master_lookup = {}

        for exp in master_experience:

            if not isinstance(
                exp,
                dict
            ):
                continue

            company = str(
                exp.get(
                    "company",
                    ""
                )
            ).strip().lower()

            if company:
                master_lookup[company] = exp

        # ----------------------------------------------------
        # Process generated experience
        # ----------------------------------------------------

        for exp in result_experience:

            if not isinstance(
                exp,
                dict
            ):
                continue

            company = str(
                exp.get(
                    "company",
                    ""
                )
            ).strip().lower()

            master_exp = master_lookup.get(
                company
            )

            if not master_exp:
                continue

            # ------------------------------------------------
            # Get generated bullets
            # ------------------------------------------------

            current_bullets = exp.get(
                "bullets",
                []
            )

            if not isinstance(
                current_bullets,
                list
            ):
                current_bullets = []

            current_bullets = [
                str(b).strip()
                for b in current_bullets
                if str(b).strip()
            ]

            # Remove exact duplicates while preserving order
            unique_bullets = []

            for bullet in current_bullets:

                if bullet not in unique_bullets:

                    unique_bullets.append(
                        bullet
                    )

            current_bullets = unique_bullets

            # ------------------------------------------------
            # Content targets
            # ------------------------------------------------

            if "tracelink" in company:

                target = 7

            elif "emotorad" in company:

                target = 5

            else:

                target = 4

            # ------------------------------------------------
            # Get canonical master bullets
            # ------------------------------------------------

            master_bullets = master_exp.get(
                "bullets",
                []
            )

            if not isinstance(
                master_bullets,
                list
            ):
                master_bullets = []

            master_bullets = [
                str(b).strip()
                for b in master_bullets
                if str(b).strip()
            ]

            # ------------------------------------------------
            # Add canonical bullets until target is reached
            # ------------------------------------------------

            for bullet in master_bullets:

                if bullet in current_bullets:
                    continue

                current_bullets.append(
                    bullet
                )

                if len(
                    current_bullets
                ) >= target:

                    break

            # ------------------------------------------------
            # HARD BULLET LIMIT
            #
            # This guarantees that the LLM cannot return
            # excessive bullets for an experience entry.
            # ------------------------------------------------

            if "tracelink" in company:

                current_bullets = current_bullets[:7]

            elif "emotorad" in company:

                current_bullets = current_bullets[:5]

            else:

                current_bullets = current_bullets[:4]

            # ------------------------------------------------
            # Save final bullets
            # ------------------------------------------------

            exp["bullets"] = current_bullets

        # ----------------------------------------------------
        # Save final experience
        # ----------------------------------------------------

        result["experience"] = result_experience

        return result
    # ========================================================
    # PROJECT NORMALIZATION
    # ========================================================

    def _normalize_projects(
        self,
        data,
        master_resume
    ):

        projects = data.get(
            "projects",
            []
        )

        if not isinstance(
            projects,
            list
        ):

            projects = []

        canonical_projects = (
            self._get_canonical_projects(
                master_resume
            )
        )

        lookup = self._project_lookup(
            master_resume
        )

        normalized = []

        for project in projects:

            if not isinstance(
                project,
                dict
            ):
                continue

            name = str(
                project.get(
                    "name",
                    ""
                )
            ).strip()

            canonical = lookup.get(
                name.lower()
            )

            if not canonical:
                continue

            current = dict(
                canonical
            )

            current.update(
                {
                    key: value
                    for key, value
                    in project.items()
                    if key != "name"
                }
            )

            bullets = current.get(
                "bullets",
                []
            )

            description = current.get(
                "description"
            )

            if (
                not bullets
                and description
            ):

                bullets = [
                    description
                ]

            if isinstance(
                bullets,
                str
            ):

                bullets = [
                    bullets
                ]

            current["bullets"] = [
                str(b).strip()
                for b in bullets
                if str(b).strip()
            ]

            normalized.append(
                current
            )

        # Fill missing projects
        used = {
            str(
                p.get(
                    "name",
                    ""
                )
            ).strip().lower()
            for p in normalized
        }

        for canonical in canonical_projects:

            if len(normalized) >= 3:
                break

            name = str(
                canonical.get(
                    "name",
                    ""
                )
            ).strip()

            if (
                not name
                or name.lower() in used
            ):
                continue

            fallback = dict(
                canonical
            )

            fallback["bullets"] = [
                str(b).strip()
                for b in fallback.get(
                    "bullets",
                    []
                )
                if str(b).strip()
            ]

            normalized.append(
                fallback
            )

            used.add(
                name.lower()
            )

        data["projects"] = normalized[:3]

        return data

    # ========================================================
    # PROJECT CONTENT FLOOR
    # ========================================================

    def _ensure_project_content_floor(
        self,
        result,
        master_resume
    ):

        lookup = self._project_lookup(
            master_resume
        )

        projects = result.get(
            "projects",
            []
        )

        for project in projects:

            if not isinstance(
                project,
                dict
            ):
                continue

            name = str(
                project.get(
                    "name",
                    ""
                )
            ).strip().lower()

            canonical = lookup.get(
                name
            )

            if not canonical:
                continue

            bullets = project.get(
                "bullets",
                []
            )

            if not isinstance(
                bullets,
                list
            ):
                bullets = []

            bullets = [
                str(b).strip()
                for b in bullets
                if str(b).strip()
            ]

            canonical_bullets = canonical.get(
                "bullets",
                []
            )

            if not isinstance(
                canonical_bullets,
                list
            ):
                canonical_bullets = []

            # Minimum 2 bullets.
            for bullet in canonical_bullets:

                if len(bullets) >= 2:
                    break

                bullet = str(
                    bullet
                ).strip()

                if (
                    bullet
                    and bullet not in bullets
                ):

                    bullets.append(
                        bullet
                    )

            # Maximum 3 bullets.
            project["bullets"] = bullets[:3]

        result["projects"] = projects

        return result

    # ========================================================
    # CERTIFICATIONS NORMALIZATION
    # ========================================================

    def _normalize_certifications(
        self,
        data,
        master_resume
    ):

        certifications = data.get(
            "certifications",
            []
        )

        if not isinstance(
            certifications,
            list
        ):

            certifications = []

        master_certifications = (
            master_resume.get(
                "certifications",
                []
            )
        )

        normalized = []

        for cert in certifications:

            if isinstance(
                cert,
                dict
            ):

                normalized.append(
                    cert
                )

                continue

            if isinstance(
                cert,
                str
            ):

                text = cert.strip()

                matched = None

                for master_cert in master_certifications:

                    if not isinstance(
                        master_cert,
                        dict
                    ):
                        continue

                    master_name = str(
                        master_cert.get(
                            "name",
                            ""
                        )
                    ).lower()

                    if (
                        master_name
                        in text.lower()
                        or text.lower()
                        in master_name
                    ):

                        matched = master_cert
                        break

                if matched:

                    normalized.append(
                        dict(matched)
                    )

                else:

                    normalized.append(
                        {
                            "name": text,
                            "issuer": "",
                            "category": ""
                        }
                    )

        # Preserve canonical certifications.
        if not normalized:

            for cert in master_certifications:

                if isinstance(
                    cert,
                    dict
                ):

                    normalized.append(
                        dict(cert)
                    )

        data["certifications"] = normalized

        return data

    # ========================================================
    # MAIN TAILOR METHOD
    # ========================================================

    def tailor(
        self,
        master_resume,
        job_description
    ):

        master_resume_json = json.dumps(
            master_resume,
            indent=2,
            ensure_ascii=False
        )

        # ====================================================
        # SYSTEM PROMPT
        # ====================================================

        system_prompt = """
You are an expert ATS resume tailoring engine.

Your task is to create a highly targeted,
factually accurate, information-dense,
ONE-PAGE resume.

The MASTER RESUME is the ONLY source of truth.

The JOB DESCRIPTION determines:

- relevance
- priority
- ordering
- emphasis
- wording

The JOB DESCRIPTION does NOT determine
how much legitimate candidate information
is displayed.

============================================================
STRICT FACTUAL ACCURACY
============================================================

NEVER invent:

- employers
- job titles
- dates
- degrees
- certifications
- projects
- technologies
- responsibilities
- achievements
- metrics
- percentages
- production deployments

The JD is NOT evidence of candidate experience.

If the JD mentions:

- Lean
- Six Sigma
- Kaizen
- Tableau
- Google Analytics
- A/B Testing
- JIRA
- Confluence
- aerospace
- manufacturing
- quality systems
- supplier quality

do NOT automatically add them.

Only use them if supported by the MASTER RESUME.

============================================================
CONTENT STRATEGY
============================================================

The goal is NOT to create the shortest possible resume.

The goal is to create a COMPLETE representation
of the candidate's legitimate capabilities.

Use this hierarchy:

1. Directly relevant master-resume facts.

2. Closely related master-resume facts.

3. Broader analytical, product, business,
   technical, operational, and stakeholder
   experience from the master resume.

4. Additional legitimate responsibilities,
   workflows, tools, and capabilities.

If the JD is short:

DO NOT make the resume short.

Instead use additional legitimate information
from the MASTER RESUME.

The JD determines PRIORITY.

The MASTER RESUME determines TRUTH.

============================================================
EXPERIENCE
============================================================

TRACE LINK:

Target 6–7 bullets.

EMOTORAD:

Target 5–6 bullets.

Each bullet should normally be 18–30 words.

Use complete professional sentences.

Prefer:

ACTION + CONTEXT + TOOL/APPROACH + PURPOSE/RESULT

when supported.

For TraceLink, prioritize supported areas such as:

- product requirements
- requirements analysis
- user stories
- acceptance criteria
- enterprise workflows
- Master Data
- administration platforms
- workflow analysis
- documentation
- process flows
- Product collaboration
- Engineering collaboration
- data quality
- validation
- governance
- compliance workflows
- AI-enabled workflow concepts
- automation opportunities

For Emotorad, prioritize supported areas such as:

- customer analysis
- product analysis
- operational analysis
- transaction analysis
- SQL
- Python
- Pandas
- Power BI
- Excel
- KPI reporting
- dashboards
- data validation
- reconciliation
- inventory
- supplier analysis
- delivery analysis
- procurement
- product listings
- stakeholder collaboration
- business recommendations

Only use areas actually supported by the
MASTER RESUME.

============================================================
PROJECTS
============================================================

Return EXACTLY 3 projects.

Projects MUST come from the canonical projects in the MASTER RESUME.

Never invent a project.

Never merge projects.

Never create a project from the JD.

For each project:

- Generate 2–3 internal supporting facts.
- The FIRST bullet MUST be a polished, concise 20–35 word project description.
- The first bullet must contain the most important technology, method, metric, and/or outcome.
- The first bullet must read naturally as a standalone resume sentence.
- Do not begin with fragments.
- Do not use unnecessary introductory phrases.

The renderer will use the FIRST bullet as the visible project description.

The remaining bullets are supporting evidence and may be used for validation or future layouts.

Example:

"Analyzed 500K+ transactions using Python, Pandas, and SQL to identify customer purchase behavior, transaction patterns, and business trends."

Use ONLY facts supported by the
MASTER RESUME.
============================================================
SKILLS
============================================================

Return 5–6 meaningful categories.

Each category should normally contain
5–8 skills.

Prioritize:

1. JD-supported skills that are genuinely
   supported by the MASTER RESUME.

2. Strong demonstrated candidate skills.

3. Broader supported skills when the JD
   is narrow.

Do not keyword stuff.

Do not add a skill merely because it appears
in the JD.

============================================================
SUMMARY
============================================================

Target approximately 55–75 words.

Target approximately 3–5 lines.

Include:

- target positioning
- strongest experience
- analytical capabilities
- technical capabilities
- relevant tools
- business/stakeholder context

============================================================
EDUCATION
============================================================

Preserve ALL canonical education.

Preserve GPA:

7.5/10

Preserve:

Class XII: 95.25%

Preserve:

Class X: 93.00%

Do not remove these values.

============================================================
CONTACT
============================================================

Preserve canonical contact information.

If the MASTER RESUME says:

Pune, India

return:

Pune, India

Never return only:

India

============================================================
CERTIFICATIONS
============================================================

Return certifications as objects:

{
    "name": "...",
    "issuer": "...",
    "category": "..."
}

============================================================
ONE-PAGE CONTENT TARGET
============================================================

The target content architecture is:

Summary:
55–75 words

Education:
2 entries

Skills:
5–6 categories

TraceLink:
6–7 bullets

Emotorad:
5–6 bullets

Projects:
exactly 3

Project bullets:
2–3 each

Certifications:
canonical certifications

If the JD is short, DO NOT reduce these targets.

Instead use additional supported information
from the MASTER RESUME.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not use Markdown.

Do not use code fences.

Do not add commentary.

Do not wrap the response inside:

"resume"

or

"tailored_resume"

The top-level JSON MUST contain:

contact
summary
skills
experience
projects
education
certifications
"""

        # ====================================================
        # USER PROMPT
        # ====================================================

        user_prompt = f"""
MASTER RESUME
============================================================

{master_resume_json}


JOB DESCRIPTION
============================================================

{job_description}


============================================================
TASK
============================================================

Create the final tailored one-page resume.

Requirements:

1. Use ONLY facts supported by the MASTER RESUME.

2. Use the JD to determine relevance and priority.

3. Do NOT make the resume short because
   the JD is short.

4. Use additional legitimate master-resume
   information when the JD is narrow.

5. TraceLink: 6–7 bullets.

6. Emotorad: 5–6 bullets.

7. Exactly 3 projects.

8. Each project: 2–3 bullets.

9. Skills: 5–6 categories.

10. Summary: approximately 55–75 words.

11. Preserve GPA 7.5/10.

12. Preserve Class XII 95.25%.

13. Preserve Class X 93.00%.

14. Preserve Pune, India.

15. Never invent candidate experience.

16. Never invent technologies.

17. Never invent projects.

18. Never invent metrics.

19. Never invent certifications.

20. Return ONLY the required JSON.
"""

        # ====================================================
        # MISTRAL
        # ====================================================

        response = self.client.chat.complete(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            max_tokens=12000,

            temperature=0,

            response_format={
                "type": "json_object"
            }
        )

        text = (
            response
            .choices[0]
            .message
            .content
        )

        if not text:

            raise RuntimeError(
                "Mistral returned an empty response."
            )

        # ====================================================
        # JSON PARSE
        # ====================================================

        try:

            data = json.loads(
                text.strip()
            )

        except json.JSONDecodeError as e:

            raise RuntimeError(
                "Mistral returned invalid JSON.\n\n"
                f"Response:\n{text}\n\n"
                f"JSON error:\n{e}"
            ) from e

        if not isinstance(
            data,
            dict
        ):

            raise RuntimeError(
                "Mistral returned a non-object JSON response."
            )

        # ====================================================
        # UNWRAP
        # ====================================================

        if (
            "tailored_resume" in data
            and isinstance(
                data["tailored_resume"],
                dict
            )
        ):

            data = data[
                "tailored_resume"
            ]

        elif (
            "resume" in data
            and isinstance(
                data["resume"],
                dict
            )
        ):

            outer_skills = data.get(
                "skills"
            )

            data = data[
                "resume"
            ]

            if (
                outer_skills
                and isinstance(
                    outer_skills,
                    dict
                )
            ):

                data["skills"] = (
                    outer_skills
                )

        # ====================================================
        # NORMALIZATION
        # ====================================================

        data = self._normalize_contact(
            data,
            master_resume
        )

        data = self._normalize_education(
            data,
            master_resume
        )

        data = self._normalize_skills(
            data,
            master_resume
        )

        data = self._normalize_experience(
            data
        )

        data = self._normalize_projects(
            data,
            master_resume
        )

        data = self._normalize_certifications(
            data,
            master_resume
        )

        # ====================================================
        # PYDANTIC VALIDATION
        # ====================================================

        try:

            validated = (
                TailoredResume.model_validate(
                    data
                )
            )

        except Exception as e:

            raise RuntimeError(
                "Mistral response does not match "
                "TailoredResume schema.\n\n"
                "Response:\n"
                f"{json.dumps(data, indent=2)}\n\n"
                "Validation error:\n"
                f"{e}"
            ) from e

        result = validated.model_dump()

        # ====================================================
        # CONTENT FLOOR
        # ====================================================

        result = (
            self._ensure_experience_content_floor(
                
                result,
                master_resume
            )
        )

        result = (
            self._ensure_project_content_floor(
                result,
                master_resume
            )
        )

        # ====================================================
        # FINAL CONTACT FIX
        # ====================================================

        master_contact = master_resume.get(
            "contact",
            {}
        )

        if isinstance(
            master_contact,
            dict
        ):

            if master_contact.get(
                "location"
            ):

                result[
                    "contact"
                ][
                    "location"
                ] = master_contact[
                    "location"
                ]

        if result[
            "contact"
        ].get(
            "location",
            ""
        ).lower() in {
            "",
            "india",
            ", india",
            "india,"
        }:

            result[
                "contact"
            ][
                "location"
            ] = "Pune, India"

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print(
            "========== CONTENT DEBUG =========="
        )

        print(
            "Experience:"
        )

        for exp in result.get(
            "experience",
            []
        ):

            print(
                f"  {exp.get('company', '')}: "
                f"{len(exp.get('bullets', []))} bullets"
            )

        print(
            f"Projects: "
            f"{len(result.get('projects', []))}"
        )

        print(
            "Skills categories:",
            len(
                result
                .get(
                    "skills",
                    {}
                )
                .get(
                    "categories",
                    {}
                )
            )
        )

        print(
            "Location:",
            result[
                "contact"
            ].get(
                "location"
            )
        )

        print(
            "=================================="
        )

        return result


# ============================================================
# FUNCTION USED BY resume_generator.py
# ============================================================

def tailor_resume(
    master_resume,
    job_description
):

    tailor = ResumeTailor()

    return tailor.tailor(
        master_resume,
        job_description
    )