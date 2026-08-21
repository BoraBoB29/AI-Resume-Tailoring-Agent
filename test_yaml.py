import yaml


with open(
    "data/master_resume.yaml",
    "r",
    encoding="utf-8"
) as file:

    resume = yaml.safe_load(file)


print("================================")
print("MASTER RESUME TEST")
print("================================")

print(
    "Name:",
    resume["contact"]["name"]
)

print(
    "Email:",
    resume["contact"]["email"]
)

print(
    "Skill Categories:",
    len(resume.get("skills", {}))
)

print(
    "Experience:",
    len(resume.get("experience", []))
)

print(
    "Projects:",
    len(resume.get("projects", []))
)

print(
    "Education:",
    len(resume.get("education", []))
)

print(
    "Certifications:",
    len(resume.get("certifications", []))
)


print()
print("================================")
print("CERTIFICATIONS")
print("================================")


for certification in resume.get(
    "certifications",
    []
):

    print(
        f"- {certification['name']}"
    )

    print(
        f"  Issuer: {certification['issuer']}"
    )

    print(
        f"  Category: {certification['category']}"
    )


print()
print("YAML TEST SUCCESS")