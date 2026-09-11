from tools.tool_registry import AVAILABLE_TOOLS


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
):
    tool = get_tool(tool_name)

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be an object."
        )

    result = tool.execute(**arguments)

    return {
        "tool_name": tool.name,
        "result": result,
    }