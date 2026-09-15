import json
from tools.tool_registry import AVAILABLE_TOOLS


MAX_TOOL_CALLS = 15


def get_tool(tool_name: str):
    tool = AVAILABLE_TOOLS.get(tool_name)

    if tool is None:
        raise ValueError(f"Unknown tool: '{tool_name}'. Available tools: {list(AVAILABLE_TOOLS.keys())}")

    return tool


def check_tool_permission(tool_name: str) -> dict:
    """Check tool risk level and whether execution requires user confirmation."""
    tool = get_tool(tool_name)
    if tool.risk_level == "confirmation_required":
        return {
            "allowed": False,
            "requires_confirmation": True,
            "tool_name": tool_name,
            "reason": f"Tool '{tool_name}' has risk level 'confirmation_required' and requires explicit user approval before execution.",
        }
    return {"allowed": True, "requires_confirmation": False, "tool_name": tool_name}


def execute_tool(
    tool_name: str,
    arguments: dict,
    user_id: int | None = None,
    project_id: int | None = None,
    db=None,
    user_confirmed: bool = False,
) -> dict:
    """Execute the specified tool cleanly and return a controlled tool result.

    Catches unknown tools, invalid argument types, missing parameters, permission checks,
    and execution failures without crashing the backend.
    """
    print("\n" + "=" * 65, flush=True)
    print(f"🔧 [GEMINI TOOL CALL REQUEST]: {tool_name}", flush=True)
    print(
        f"📥 [ARGUMENTS]:\n{json.dumps(arguments if isinstance(arguments, dict) else str(arguments), indent=2, default=str)}",
        flush=True,
    )
    print("-" * 65, flush=True)

    try:
        tool = get_tool(tool_name)

        if not isinstance(arguments, dict):
            result = {
                "success": False,
                "error": f"Invalid arguments format. Expected a dictionary object, got {type(arguments).__name__}.",
            }
        else:
            perm_check = check_tool_permission(tool_name)
            if not perm_check["allowed"] and not user_confirmed:
                result = {
                    "success": False,
                    "requires_confirmation": True,
                    "error": perm_check["reason"],
                }
            else:
                exec_kwargs = dict(arguments)
                # Remove any model-supplied context parameters to prevent context spoofing
                for forbidden_key in ("user_id", "project_id", "db", "_user_id", "_project_id", "_db"):
                    exec_kwargs.pop(forbidden_key, None)

                if user_id is not None:
                    exec_kwargs["_user_id"] = user_id
                if project_id is not None:
                    exec_kwargs["_project_id"] = project_id
                if db is not None:
                    exec_kwargs["_db"] = db

                result = tool.execute(**exec_kwargs)

    except Exception as error:
        result = {
            "success": False,
            "error": str(error),
        }

    tool_response = {
        "tool_name": tool_name,
        "result": result,
    }

    print(
        f"📤 [TOOL EXECUTION RESULT RESPONSE]:\n{json.dumps(tool_response, indent=2, default=str)}",
        flush=True,
    )
    print("=" * 65 + "\n", flush=True)

    return tool_response