import sys

if "pytest" in sys.modules:
    import pytest

    pytest.skip(
        "Manual Mistral model-availability smoke script; run directly "
        "(`python test_mistral_models.py`) when API access is intended. "
        "Not run under pytest since it makes real, billed API calls.",
        allow_module_level=True,
    )

from mistralai.client import Mistral
import os
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

models = [
    "mistral-medium-2505",
    "mistral-medium-2508",
    "mistral-small-2603",
    "mistral-small-latest",
    "ministral-3b-latest",
    "ministral-8b-latest",
    "ministral-14b-latest",
]

for model in models:
    try:
        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "user", "content": "Reply with exactly OK"}
            ],
        )
        print(f"{model}: OK -> {response.choices[0].message.content}")
    except Exception as e:
        print(f"{model}: FAILED -> {e}")