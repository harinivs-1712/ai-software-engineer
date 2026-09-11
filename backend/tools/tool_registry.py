from tools.calculator import CalculatorTool


calculator_tool = CalculatorTool()

AVAILABLE_TOOLS = {
    calculator_tool.name: calculator_tool,
}


def get_tool_definitions():
    return [
        tool.get_definition()
        for tool in AVAILABLE_TOOLS.values()
    ]