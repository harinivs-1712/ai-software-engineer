from prompts.base import BASE_SYSTEM_PROMPT

from prompts.generate import GENERATE_PROMPT
from prompts.debug import DEBUG_PROMPT
from prompts.explain import EXPLAIN_PROMPT
from prompts.review import REVIEW_PROMPT
from prompts.refactor import REFACTOR_PROMPT
from prompts.documentation import DOCUMENTATION_PROMPT
from prompts.testing import TESTING_PROMPT

PROMPTS = {

    "generate": GENERATE_PROMPT,

    "debug": DEBUG_PROMPT,

    "explain": EXPLAIN_PROMPT,

    "review": REVIEW_PROMPT,

    "refactor": REFACTOR_PROMPT,

    "documentation": DOCUMENTATION_PROMPT,

    "testing": TESTING_PROMPT,
}

def get_system_prompt(mode: str) -> str:

    mode = mode.lower().strip()

    if mode not in PROMPTS:
        mode = "generate"

    return (
        BASE_SYSTEM_PROMPT
        + "\n\n"
        + PROMPTS[mode]
    )
    
AVAILABLE_MODES = {
    "generate",
    "debug",
    "explain",
    "review",
    "refactor",
    "documentation",
    "testing",
}

def get_system_prompt(mode: str) -> str:

    mode = mode.lower().strip()

    if mode not in AVAILABLE_MODES:
        raise ValueError(
            f"Unsupported mode: {mode}"
        )

    return (
        BASE_SYSTEM_PROMPT
        + "\n\n"
        + PROMPTS[mode]
    )