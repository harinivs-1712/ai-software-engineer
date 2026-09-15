from tools.tool_registry import AVAILABLE_TOOLS


import json


MAX_TOOL_CALLS = 15


def get_tool(tool_name: str):
    tool = AVAILABLE_TOOLS.get(tool_name)

    if tool is None:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    return tool


def execute_tool(
    tool_name: str,
    arguments: dict,
    user_id: int | None = None,
    project_id: int | None = None,
    db = None,
):
    tool = get_tool(tool_name)

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be an object."
        )

    exec_kwargs = dict(arguments)
    if user_id is not None:
        exec_kwargs["_user_id"] = user_id
    if project_id is not None:
        exec_kwargs["_project_id"] = project_id
    if db is not None:
        exec_kwargs["_db"] = db

    print("\n" + "=" * 65, flush=True)
    print(f"🔧 [GEMINI TOOL CALL REQUEST]: {tool_name}", flush=True)
    print(f"📥 [ARGUMENTS]:\n{json.dumps(arguments, indent=2, default=str)}", flush=True)
    print("-" * 65, flush=True)

    result = tool.execute(**exec_kwargs)

    tool_response = {
        "tool_name": tool.name,
        "result": result,
    }

    print(f"📤 [TOOL EXECUTION RESULT RESPONSE]:\n{json.dumps(tool_response, indent=2, default=str)}", flush=True)
    print("=" * 65 + "\n", flush=True)

    return tool_response