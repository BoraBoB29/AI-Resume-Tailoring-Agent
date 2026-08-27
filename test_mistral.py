import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual Mistral smoke script; run directly when API access is intended.",
        allow_module_level=True,
    )

import os

from dotenv import load_dotenv
from mistralai.client import Mistral


# Load .env
load_dotenv(
    ".env",
    override=True
)


# Get configuration
api_key = os.getenv(
    "MISTRAL_API_KEY"
)

model = os.getenv(
    "MISTRAL_MODEL",
    "mistral-large-latest"
)


print()
print("==============================")
print("MISTRAL API TEST")
print("==============================")

print(
    "API Key:",
    "FOUND" if api_key else "NOT FOUND"
)

print(
    "Model:",
    model
)


if not api_key:

    raise RuntimeError(
        "MISTRAL_API_KEY was not found."
    )


# Create Mistral client
client = Mistral(
    api_key=api_key
)


# Send test request
response = client.chat.complete(

    model=model,

    messages=[
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "MISTRAL TEST SUCCESS"
            )
        }
    ],

    max_tokens=50
)


print()
print("==============================")
print("RESPONSE")
print("==============================")


print(
    response.choices[0].message.content
)