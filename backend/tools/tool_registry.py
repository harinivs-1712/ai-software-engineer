from tools.calculator import CalculatorTool
from tools.code_executor import CodeExecutorTool
from tools.list_files import ListFilesTool
from tools.read_file import ReadFileTool
from tools.search_files import SearchFilesTool
from tools.get_file_info import GetFileInfoTool


calculator_tool = CalculatorTool()
code_executor_tool = CodeExecutorTool()
list_files_tool = ListFilesTool()
read_file_tool = ReadFileTool()
search_files_tool = SearchFilesTool()
get_file_info_tool = GetFileInfoTool()


AVAILABLE_TOOLS = {
    calculator_tool.name: calculator_tool,
    code_executor_tool.name: code_executor_tool,
    list_files_tool.name: list_files_tool,
    read_file_tool.name: read_file_tool,
    search_files_tool.name: search_files_tool,
    get_file_info_tool.name: get_file_info_tool,
}


def get_tool_definitions():
    return [
        tool.get_definition()
        for tool in AVAILABLE_TOOLS.values()
    ]