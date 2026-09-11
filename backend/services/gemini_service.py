from collections.abc import Iterator
import time
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME
from services.prompt_manager import get_system_prompt
from services.tool_service import execute_tool
from tools.tool_registry import get_tool_definitions

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not configured.")


client = genai.Client(api_key=GEMINI_API_KEY)


def build_contents(history, message=None):
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

    if message:
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

    contents = build_contents(history, final_message)
    system_prompt = get_system_prompt(mode)

    tools_config = [types.Tool(function_declarations=get_tool_definitions())]

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=tools_config,
    )

    models_to_try = [MODEL_NAME, "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.7-flash"]
    seen_models = set()
    active_models = []
    for m in models_to_try:
        if m and m not in seen_models:
            seen_models.add(m)
            active_models.append(m)

    last_error = None

    for target_model in active_models:
        for attempt in range(2):
            try:
                # Phase 1: Check for initial function call before streaming text
                initial_check = client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=tools_config,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )

                function_calls = getattr(initial_check, "function_calls", None)

                if function_calls:
                    # De-duplicate tool names for clean formatting
                    unique_tools = []
                    seen_tools = set()
                    for fc in function_calls:
                        tool_name = fc.name.replace("_", " ").title()
                        if tool_name not in seen_tools:
                            seen_tools.add(tool_name)
                            unique_tools.append(tool_name)

                    tool_str = ", ".join(unique_tools)
                    suffix = "Tool" if len(unique_tools) == 1 else "Tools"
                    yield f"🛠️ *Used {tool_str} {suffix}*\n\n"

                    if initial_check.candidates and initial_check.candidates[0].content:
                        contents.append(initial_check.candidates[0].content)

                    # Function Call Branch: execute tool & construct function response part
                    for function_call in function_calls:
                        args = function_call.args if hasattr(function_call, "args") else {}
                        result = execute_tool(
                            function_call.name,
                            args,
                        )

                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=function_call.name,
                                        response=result,
                                    )
                                ],
                            )
                        )

                    # Stream final response after tool execution
                    stream = client.models.generate_content_stream(
                        model=target_model,
                        contents=contents,
                        config=config,
                    )
                    for chunk in stream:
                        if chunk.text:
                            yield chunk.text
                    return

                # Direct Stream Branch (No Function Call Needed)
                stream = client.models.generate_content_stream(
                    model=target_model,
                    contents=contents,
                    config=config,
                )
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text
                return

            except Exception as exc:
                last_error = exc
                err_msg = str(exc)
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
                    time.sleep(1)
                    continue
                else:
                    break

    yield f"\n[Error communicating with Gemini: {str(last_error)}]"
    
    
def build_gemini_tools():
    return [types.Tool(function_declarations=get_tool_definitions())]
    
def generate_response_with_tools(
    message: str,
    history,
    mode: str,
    project_context: str = "",
):
    contents = build_contents(
        history,
        message,
    )

    system_prompt = get_system_prompt(mode)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=build_gemini_tools(),
        automatic_function_calling=(
            types.AutomaticFunctionCallingConfig(
                disable=True
            )
        ),
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=config,
    )

    # -------------------------
    # No tool requested
    # -------------------------

    if not response.function_calls:
        return response.text

    # -------------------------
    # Tool requested
    # -------------------------

    contents.append(
        response.candidates[0].content
    )

    for function_call in response.function_calls:

        tool_name = function_call.name
        arguments = function_call.args or {}

        tool_result = execute_tool(
            tool_name,
            arguments,
        )

        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=tool_name,
                        response=tool_result,
                        id=function_call.id,
                    )
                ],
            )
        )

    # -------------------------
    # Send result back to Gemini
    # -------------------------

    final_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=config,
    )

    return final_response.text
