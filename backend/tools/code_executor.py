from tools.base import BaseTool
from services.code_execution_service import (
    execute_python,
)


class CodeExecutorTool(BaseTool):

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return (
            "Execute Python source code in an isolated sandbox environment. "
            "Use this tool whenever you need to run Python code, execute scripts, "
            "verify algorithms, test Python expressions, or get real runtime output "
            "(stdout, stderr, exit_code)."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": (
                        "Complete Python source code "
                        "to execute."
                    ),
                },
                "timeout": {
                    "type": "integer",
                    "description": (
                        "Maximum execution time in seconds."
                    ),
                },
            },
            "required": ["code"],
        }

    def execute(self, **kwargs):

        code = kwargs.get("code")

        timeout = kwargs.get(
            "timeout",
            5,
        )

        return execute_python(
            code=code,
            timeout=timeout,
        )
