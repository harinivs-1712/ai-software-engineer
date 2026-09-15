from collections.abc import Iterator
import time
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME
from services.prompt_manager import get_system_prompt
from services.tool_service import execute_tool, MAX_TOOL_CALLS
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


def build_gemini_tools():
    return [types.Tool(function_declarations=get_tool_definitions())]


def generate_response_with_tools(
    message: str,
    history,
    mode: str,
    project_context: str = "",
    user_id: int | None = None,
    project_id: int | None = None,
    db = None,
):
    contents = build_contents(
        history,
        message,
    )

    system_prompt = get_system_prompt(mode)

    if project_context:
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=(
                            "Project context:\n\n"
                            + project_context
                        )
                    )
                ],
            )
        )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=build_gemini_tools(),
        automatic_function_calling=(
            types.AutomaticFunctionCallingConfig(
                disable=True
            )
        ),
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
                tool_call_count = 0

                while True:

                    # --------------------------------
                    # Ask Gemini what to do
                    # --------------------------------

                    response = client.models.generate_content(
                        model=target_model,
                        contents=contents,
                        config=config,
                    )

                    # --------------------------------
                    # No tool call
                    # --------------------------------

                    if not response.function_calls:
                        return response.text

                    # --------------------------------
                    # Tool call detected
                    # --------------------------------

                    if tool_call_count >= MAX_TOOL_CALLS:
                        return (
                            "I reached the maximum number of "
                            "tool executions allowed for this request."
                        )

                    # Preserve Gemini's tool-call response
                    if response.candidates and response.candidates[0].content:
                        contents.append(
                            response.candidates[0].content
                        )

                    # --------------------------------
                    # Execute every requested tool
                    # --------------------------------

                    for function_call in response.function_calls:

                        tool_call_count += 1

                        if tool_call_count > MAX_TOOL_CALLS:
                            break

                        tool_name = function_call.name
                        arguments = function_call.args or {}

                        try:
                            tool_result = execute_tool(
                                tool_name,
                                arguments,
                                user_id=user_id,
                                project_id=project_id,
                                db=db,
                            )

                        except Exception as error:
                            tool_result = {
                                "tool_name": tool_name,
                                "result": {
                                    "success": False,
                                    "error": str(error),
                                },
                            }

                        # --------------------------------
                        # Inject tool result into Gemini
                        # --------------------------------

                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=tool_name,
                                        response=tool_result,
                                    )
                                ],
                            )
                        )

            except Exception as exc:
                last_error = exc
                err_msg = str(exc)
                if any(k in err_msg for k in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand", "Quota exceeded"]):
                    time.sleep(1)
                    continue
                else:
                    break

    return f"[Error communicating with Gemini: {str(last_error)}]"


def generate_response_stream(
    message: str,
    history,
    mode: str,
    project_context: str = "",
    user_id: int | None = None,
    project_id: int | None = None,
    db = None,
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

    tools_config = build_gemini_tools()

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
                tool_call_count = 0
                reported_tool_names = set()

                while True:
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

                    if not function_calls:
                        # Model is done calling tools, stream final answer
                        stream = client.models.generate_content_stream(
                            model=target_model,
                            contents=contents,
                            config=config,
                        )
                        for chunk in stream:
                            if chunk.text:
                                yield chunk.text
                        return

                    if tool_call_count >= MAX_TOOL_CALLS:
                        yield f"\n[Reached maximum number of tool executions allowed ({MAX_TOOL_CALLS})]"
                        return

                    # Format visual badge for newly invoked tools in this request
                    new_tools = []
                    for fc in function_calls:
                        t_name = fc.name
                        if t_name not in reported_tool_names:
                            reported_tool_names.add(t_name)
                            new_tools.append(t_name.replace("_", " ").title())

                    if new_tools:
                        tool_str = ", ".join(new_tools)
                        suffix = "Tool" if len(new_tools) == 1 else "Tools"
                        yield f"🛠️ *Used {tool_str} {suffix}*\n\n"

                    if initial_check.candidates and initial_check.candidates[0].content:
                        contents.append(initial_check.candidates[0].content)

                    for function_call in function_calls:
                        tool_call_count += 1
                        if tool_call_count > MAX_TOOL_CALLS:
                            break

                        tool_name = function_call.name
                        args = function_call.args if hasattr(function_call, "args") else {}

                        try:
                            tool_result = execute_tool(
                                tool_name,
                                args,
                                user_id=user_id,
                                project_id=project_id,
                                db=db,
                            )
                        except Exception as error:
                            tool_result = {
                                "tool_name": tool_name,
                                "result": {
                                    "success": False,
                                    "error": str(error),
                                },
                            }

                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=tool_name,
                                        response=tool_result,
                                    )
                                ],
                            )
                        )

            except Exception as exc:
                last_error = exc
                err_msg = str(exc)
                if any(k in err_msg for k in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand", "Quota exceeded"]):
                    time.sleep(1)
                    continue
                else:
                    break

    yield f"\n[Error communicating with Gemini: {str(last_error)}]"
