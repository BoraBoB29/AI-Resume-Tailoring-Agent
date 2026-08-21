import re
from pathlib import Path


def escape_latex(text):

    if text is None:
        return ""

    text = str(text)

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    return text


# ============================================================
# CONTACT
# ============================================================

def format_contact(contact):

    name = escape_latex(
        contact.get(
            "name",
            ""
        )
    )

    email = escape_latex(
        contact.get(
            "email",
            ""
        )
    )

    phone = escape_latex(
        contact.get(
            "phone",
            ""
        )
    )

    linkedin = escape_latex(
        contact.get(
            "linkedin",
            ""
        )
    )

    location = escape_latex(
        contact.get(
            "location",
            ""
        )
    )

    return rf"""
\begin{{center}}

{{\LARGE \bfseries \color{{accent}} {name}}}

\vspace{{2pt}}

\footnotesize

\href{{mailto:{email}}}{{{email}}}
\quad$|$\quad
{phone}
\quad$|$\quad
\href{{https://{linkedin}}}{{{linkedin}}}
\quad$|$\quad
{location}

\end{{center}}

\vspace{{-4pt}}
"""


# ============================================================
# SUMMARY
# ============================================================

def format_summary(summary):

    if not summary:
        return ""

    return (
        "\\small\n"
        + escape_latex(summary)
        + "\n"
    )


# ============================================================
# EDUCATION
# ============================================================

def format_education(education):

    output = []

    for index, edu in enumerate(
        education
    ):

        institution = escape_latex(
            edu.get(
                "institution",
                ""
            )
        )

        degree = escape_latex(
            edu.get(
                "degree",
                ""
            )
        )

        location = escape_latex(
            edu.get(
                "location",
                ""
            )
        )

        start_date = escape_latex(
            edu.get(
                "start_date",
                ""
            )
        )

        end_date = escape_latex(
            edu.get(
                "end_date",
                ""
            )
        )

        gpa = edu.get(
            "gpa"
        )

        date_text = (
            f"{start_date} – {end_date}"
            if start_date or end_date
            else ""
        )

        output.append(
            rf"""
\noindent
\textbf{{{institution}}}
\hfill
\textit{{\small {date_text}}}

\\[-1pt]

\textit{{\small {degree}}}
\hfill
\small {location}
"""
        )

        if gpa:

            output.append(
                rf"""
\\[-1pt]
\small
GPA: {escape_latex(gpa)}
"""
            )

        # Gap between education entries
        if index < len(education) - 1:

            output.append(
                r"\vspace{4pt}"
            )

    return "\n".join(
        output
    )


# ============================================================
# SKILLS
# ============================================================

def format_skills(skills):

    categories = skills.get(
        "categories",
        {}
    )

    if not isinstance(
        categories,
        dict
    ):
        return ""

    output = []

    for category, values in categories.items():

        if not values:
            continue

        category_text = escape_latex(
            category
        )

        skills_text = ", ".join(
            escape_latex(
                value
            )
            for value in values
        )

        output.append(
            rf"""
\resumeItem{{
\textbf{{{category_text}:}}
{skills_text}
}}
"""
        )

    return "\n".join(
        output
    )


# ============================================================
# EXPERIENCE
# ============================================================

def format_experience(experience):

    output = []

    for index, exp in enumerate(
        experience
    ):

        company = escape_latex(
            exp.get(
                "company",
                ""
            )
        )

        title = escape_latex(
            exp.get(
                "title",
                ""
            )
        )

        location = escape_latex(
            exp.get(
                "location",
                ""
            )
        )

        start_date = escape_latex(
            exp.get(
                "start_date",
                ""
            )
        )

        end_date = escape_latex(
            exp.get(
                "end_date",
                ""
            )
        )

        output.append(
            rf"""
\resumeEntry
{{{company}}}
{{{start_date} – {end_date}}}
{{{title}}}
{{{location}}}
"""
        )

        output.append(
            r"\begin{resumeItemize}"
        )

        for bullet in exp.get(
            "bullets",
            []
        ):

            output.append(
                rf"\resumeItem{{{escape_latex(bullet)}}}"
            )

        output.append(
            r"\end{resumeItemize}"
        )

        # Gap between experiences
        if index < len(experience) - 1:

            output.append(
                r"\vspace{4pt}"
            )

    return "\n".join(
        output
    )


# ============================================================
# PROJECTS
# ============================================================

def format_projects(projects):
    """
    Render projects as:

    • Project Title - Description

    Each project is one bullet.
    The title is bold.
    The description is a single concise sentence.
    The description may naturally wrap to a second line.
    """

    output = []

    for index, project in enumerate(projects):

        if not isinstance(project, dict):
            continue

        # --------------------------------------------------
        # PROJECT TITLE
        # --------------------------------------------------

        name = str(
            project.get("name", "")
        ).strip()

        if not name:
            continue

        # --------------------------------------------------
        # PROJECT DESCRIPTION
        # --------------------------------------------------

        bullets = project.get(
            "bullets",
            []
        )

        if not isinstance(
            bullets,
            list
        ):
            bullets = []

        descriptions = [
            str(b).strip()
            for b in bullets
            if str(b).strip()
        ]

        if not descriptions:
            continue

        # Use ONLY the first bullet as the visible
        # project description.
        description = descriptions[0]

        # --------------------------------------------------
        # RENDER ONE PROJECT = ONE BULLET
        # --------------------------------------------------

        output.append(
            rf"""
\resumeItem{{
    \textbf{{{escape_latex(name)}}}
    -
    {escape_latex(description)}
}}
"""
        )

        # --------------------------------------------------
        # SMALL GAP BETWEEN PROJECTS
        # --------------------------------------------------

        if index < len(projects) - 1:

            output.append(
                r"\vspace{2pt}"
            )

    return "\n".join(output)


# ============================================================
# CERTIFICATIONS
# ============================================================

def format_certifications(
    certifications
):

    output = []

    for cert in certifications:

        if isinstance(
            cert,
            dict
        ):

            name = escape_latex(
                cert.get(
                    "name",
                    ""
                )
            )

            issuer = escape_latex(
                cert.get(
                    "issuer",
                    ""
                )
            )

            if issuer:

                output.append(
                    f"{name} ({issuer})"
                )

            else:

                output.append(
                    name
                )

        else:

            output.append(
                escape_latex(cert)
            )

    if not output:
        return ""

    return ", ".join(
        output
    )


# ============================================================
# RENDER
# ============================================================

def render_latex(
    tailored,
    template_path,
    output_path
):

    template_path = Path(
        template_path
    )

    output_path = Path(
        output_path
    )

    template = template_path.read_text(
        encoding="utf-8"
    )

    contact = format_contact(
        tailored.get(
            "contact",
            {}
        )
    )

    summary = format_summary(
        tailored.get(
            "summary",
            ""
        )
    )

    education = format_education(
        tailored.get(
            "education",
            []
        )
    )

    skills = format_skills(
        tailored.get(
            "skills",
            {}
        )
    )

    experience = format_experience(
        tailored.get(
            "experience",
            []
        )
    )

    projects = format_projects(
        tailored.get(
            "projects",
            []
        )
    )

    # --------------------------------------------------------
    # Certifications are intentionally not a separate section
    # if your template does not contain one.
    #
    # If your template later includes <<CERTIFICATIONS>>,
    # this value is ready.
    # --------------------------------------------------------

    certifications = format_certifications(
        tailored.get(
            "certifications",
            []
        )
    )

    replacements = {

        "<<CONTACT>>":
            contact,

        "<<SUMMARY>>":
            summary,

        "<<EDUCATION>>":
            education,

        "<<SKILLS>>":
            skills,

        "<<EXPERIENCE>>":
            experience,

        "<<PROJECTS>>":
            projects,

        "<<CERTIFICATIONS>>":
            certifications,
    }

    for placeholder, value in replacements.items():

        template = template.replace(
            placeholder,
            value
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        template,
        encoding="utf-8"
    )

    return output_path