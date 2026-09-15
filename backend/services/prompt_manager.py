from prompts.base import BASE_SYSTEM_PROMPT

from prompts.generate import GENERATE_PROMPT
from prompts.debug import DEBUG_PROMPT
from prompts.explain import EXPLAIN_PROMPT
from prompts.review import REVIEW_PROMPT
from prompts.refactor import REFACTOR_PROMPT
from prompts.documentation import DOCUMENTATION_PROMPT
from prompts.testing import TESTING_PROMPT
from prompts.software_engineer import SYSTEM_PROMPT as SOFTWARE_ENGINEER_PROMPT

PROMPTS = {
    "generate": GENERATE_PROMPT,
    "debug": DEBUG_PROMPT,
    "explain": EXPLAIN_PROMPT,
    "review": REVIEW_PROMPT,
    "refactor": REFACTOR_PROMPT,
    "documentation": DOCUMENTATION_PROMPT,
    "testing": TESTING_PROMPT,
    "software_engineer": SOFTWARE_ENGINEER_PROMPT,
}

AVAILABLE_MODES = set(PROMPTS.keys())

def get_system_prompt(mode: str = "generate", project_context: str | None = None) -> str:
    """Construct the final system prompt following Phase 3 Architecture:

    Global Tool-Aware System Prompt
                   +
    Mode-Specific Prompt
                   +
    Project Context (if available)
    """
    if not mode:
        mode = "generate"
    mode = str(mode).lower().strip()

    if mode not in PROMPTS:
        mode = "generate"

    prompt = BASE_SYSTEM_PROMPT.strip() + "\n\n" + PROMPTS[mode].strip()

    if project_context and str(project_context).strip():
        prompt += "\n\nCURRENT PROJECT CONTEXT:\n" + str(project_context).strip()

    return prompt