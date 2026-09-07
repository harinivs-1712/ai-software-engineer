
from collections.abc import Iterator

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME

from services.prompt_manager import (
    get_system_prompt
)


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def build_contents(history, message):
    raw_turns = []

    if history:
        for item in history:
            item_role = getattr(item, "role", None) if hasattr(item, "role") else (item.get("role") if isinstance(item, dict) else "user")
            item_content = getattr(item, "content", "") if hasattr(item, "content") else (item.get("content", "") if isinstance(item, dict) else "")

            text_str = str(item_content or "").strip()
            if not text_str:
                continue

            role = "model" if item_role == "assistant" else "user"
            raw_turns.append({"role": role, "text": text_str})

    msg_str = str(message or "").strip()
    if msg_str:
        raw_turns.append({"role": "user", "text": msg_str})

    merged_turns = []
    for turn in raw_turns:
        if merged_turns and merged_turns[-1]["role"] == turn["role"]:
            merged_turns[-1]["text"] += "\n\n" + turn["text"]
        else:
            merged_turns.append(turn)

    while merged_turns and merged_turns[0]["role"] != "user":
        merged_turns.pop(0)

    contents = [
        types.Content(
            role=turn["role"],
            parts=[types.Part(text=turn["text"])],
        )
        for turn in merged_turns
    ]

    return contents


def generate_response_stream(
    message: str,
    history,
    mode: str,
    project_context: str = "",
) -> Iterator[str]:

    final_message = message

    if project_context:
        final_message = f"""
You are working with the user's uploaded software project.

Use the project context below when answering the user's question.

PROJECT CONTEXT:

{project_context}

USER QUESTION:

{message}

Instructions:
- Use the provided project context when relevant.
- Do not assume files or code that were not provided.
- Clearly identify relevant files when discussing the project.
- If the available project context is insufficient, say so.
"""

    contents = build_contents(
        history,
        final_message
    )

    system_prompt = get_system_prompt(mode)

    try:
        response_stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    except Exception as exc:
        err_msg = str(exc)
        if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
            # Fallback to alternate models if available
            fallback_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            for alt_model in fallback_models:
                if alt_model == MODEL_NAME:
                    continue
                try:
                    alt_stream = client.models.generate_content_stream(
                        model=alt_model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt
                        )
                    )
                    for chunk in alt_stream:
                        if chunk.text:
                            yield chunk.text
                    return
                except Exception:
                    continue
        yield f"\n[Error communicating with Gemini: {err_msg}]"


