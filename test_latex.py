import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual LaTeX smoke script; run directly when compilation is intended.",
        allow_module_level=True,
    )

import subprocess
from pathlib import Path


output_dir = Path("output/tex")
output_dir.mkdir(
    parents=True,
    exist_ok=True
)

tex_file = output_dir / "test.tex"

tex_content = r"""
\documentclass[10pt,letterpaper]{article}

\usepackage[left=0.48in,right=0.48in,top=0.32in,bottom=0.28in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage[T1]{fontenc}
\usepackage{newtxtext}
\usepackage{newtxmath}
\usepackage{xcolor}

\renewcommand{\familydefault}{\sfdefault}

\definecolor{accent}{HTML}{1F3864}

\pagestyle{empty}

\begin{document}

\begin{center}

{\LARGE \bfseries \color{accent} Varun Bora}\\[3pt]

\footnotesize

varunbora03@gmail.com
\quad$|$\quad
+91 9140758437
\quad$|$\quad
Pune, India

\end{center}

\section*{Summary}

This is a test of the automated resume generation system.

\section*{Skills}

\begin{itemize}

\item Python, SQL, Pandas, Power BI

\item Certifications:
Google Data Analytics Professional Certificate;
SQL Intermediate;
Python Programming;
Enterprise Automation

\end{itemize}

\end{document}
"""

tex_file.write_text(
    tex_content,
    encoding="utf-8"
)

print("Compiling:", tex_file)

result = subprocess.run(
    [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory",
        str(output_dir),
        str(tex_file)
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:

    print()
    print("==============================")
    print("LATEX TEST SUCCESS")
    print("==============================")

    print(
        "PDF:",
        output_dir / "test.pdf"
    )

else:

    print()
    print("==============================")
    print("LATEX TEST FAILED")
    print("==============================")

    print(result.stdout)
    print(result.stderr)