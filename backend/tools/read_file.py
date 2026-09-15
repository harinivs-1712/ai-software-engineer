from tools.base import BaseTool
from services.file_system_service import read_project_file


class ReadFileTool(BaseTool):

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the complete or line-range contents of a specific project file."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Project-relative path of the file to read (e.g. 'backend/auth.py').",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional line number to start reading from (1-indexed).",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional line number to stop reading at (inclusive).",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs):
        # Strictly use trusted context attached by backend (ignore model-supplied user/project IDs)
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("_project_id")
        path = kwargs.get("path")
        start_line = kwargs.get("start_line")
        end_line = kwargs.get("end_line")

        if not isinstance(path, str) or not path.strip():
            return {
                "success": False,
                "error": "Path must be a non-empty string.",
            }

        if start_line is not None:
            if not isinstance(start_line, int) or isinstance(start_line, bool) or start_line < 1:
                return {
                    "success": False,
                    "error": "start_line must be a positive integer.",
                }

        if end_line is not None:
            if not isinstance(end_line, int) or isinstance(end_line, bool) or end_line < 1:
                return {
                    "success": False,
                    "error": "end_line must be a positive integer.",
                }

        if start_line is not None and end_line is not None and start_line > end_line:
            return {
                "success": False,
                "error": "start_line cannot be greater than end_line.",
            }

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "No active project is selected for this conversation.",
            }

        try:
            return read_project_file(
                db=db,
                user_id=user_id,
                project_id=project_id,
                path=path,
                start_line=start_line,
                end_line=end_line,
            )
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
