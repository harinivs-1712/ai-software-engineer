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
    def risk_level(self) -> str:
        return "restricted"

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
        timeout = kwargs.get("timeout", 5)

        if not isinstance(code, str) or not code.strip():
            return {
                "success": False,
                "error": "Code must be a non-empty string.",
            }

        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 30:
            return {
                "success": False,
                "error": "Timeout must be an integer between 1 and 30 seconds.",
            }

        try:
            return execute_python(
                code=code,
                timeout=timeout,
            )
        except Exception as error:
            return {
                "success": False,
                "error": f"Code execution failed: {str(error)}",
            }
