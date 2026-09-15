from tools.base import BaseTool
from services.file_system_service import get_project_file_info


class GetFileInfoTool(BaseTool):

    @property
    def name(self) -> str:
        return "get_file_info"

    @property
    def description(self) -> str:
        return (
            "Retrieve basic file metadata (size, extension, line_count) for a file in the currently selected project."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Project-relative path of the file to inspect (e.g. 'backend/auth.py').",
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

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "No active project is selected for this conversation.",
            }

        try:
            return get_project_file_info(
                db=db,
                user_id=user_id,
                project_id=project_id,
                path=path,
            )
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
