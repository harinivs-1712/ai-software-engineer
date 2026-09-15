from tools.base import BaseTool
from services.file_system_service import list_project_files


class ListFilesTool(BaseTool):

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return (
            "List files available inside the currently selected project."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs):
        # Strictly use trusted context attached by backend (ignore model-supplied user/project IDs)
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("_project_id")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "No active project is selected for this conversation.",
            }

        try:
            return list_project_files(
                db=db,
                user_id=user_id,
                project_id=project_id,
            )
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
