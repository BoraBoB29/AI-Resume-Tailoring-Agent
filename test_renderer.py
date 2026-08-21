from pathlib import Path
import yaml

from src.latex_renderer import LatexRenderer


MASTER_RESUME = Path(
    "data/master_resume.yaml"
)


with open(
    MASTER_RESUME,
    "r",
    encoding="utf-8"
) as file:

    resume = yaml.safe_load(file)


renderer = LatexRenderer()

output = renderer.render(
    resume,
    "master_resume_test.tex"
)


print()
print("==============================")
print("RENDERER TEST SUCCESS")
print("==============================")

print(
    "Generated:",
    output
)

print(
    "Certifications:",
    len(
        resume.get(
            "certifications",
            []
        )
    )
)