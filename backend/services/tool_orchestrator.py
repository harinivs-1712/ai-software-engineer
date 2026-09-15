import concurrent.futures
from typing import Any, Dict, List, Tuple
from services.tool_service import execute_tool


class ToolOrchestrator:
    """Tool Orchestrator layer.

    Responsible for managing single, sequential, parallel, and mixed tool execution workflows.
    Decouples execution orchestration from individual tool implementations.
    """

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def _execute_single(
        self,
        function_call: Any,
        user_id: int | None = None,
        project_id: int | None = None,
        db=None,
    ) -> Tuple[str, Dict[str, Any]]:
        tool_name = function_call.name
        args = function_call.args if hasattr(function_call, "args") else {}

        try:
            tool_result = execute_tool(
                tool_name=tool_name,
                arguments=args,
                user_id=user_id,
                project_id=project_id,
                db=db,
            )
        except Exception as error:
            tool_result = {
                "tool_name": tool_name,
                "arguments": args,
                "result": {
                    "success": False,
                    "error": str(error),
                },
            }

        return tool_name, tool_result

    def orchestrate_tool_calls(
        self,
        function_calls: List[Any],
        user_id: int | None = None,
        project_id: int | None = None,
        db=None,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Orchestrate tool executions across sequential, parallel, and mixed workflows.

        - Single call: Executed directly.
        - Multiple independent calls in a turn: Executed concurrently in parallel.
        - Combines results with clear tool name and parameters mapping.
        """
        if not function_calls:
            return []

        if len(function_calls) == 1:
            return [
                self._execute_single(
                    function_call=function_calls[0],
                    user_id=user_id,
                    project_id=project_id,
                    db=db,
                )
            ]

        # Parallel execution of independent tool calls in current turn
        workers = min(len(function_calls), self.max_workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    self._execute_single,
                    fc,
                    user_id,
                    project_id,
                    db,
                )
                for fc in function_calls
            ]
            return [future.result() for future in concurrent.futures.as_completed(futures)]
