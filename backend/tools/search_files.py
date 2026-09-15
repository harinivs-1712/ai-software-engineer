from tools.base import BaseTool
from services.file_system_service import search_project_files


class SearchFilesTool(BaseTool):

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return (
            "Search for a text string or code query across all files in the currently selected project."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text substring or pattern to search for in project files.",
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs):
        # Strictly use trusted context attached by backend (ignore model-supplied user/project IDs)
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("_project_id")
        query = kwargs.get("query")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "No active project is selected for this conversation.",
            }

        try:
            return search_project_files(
                db=db,
                user_id=user_id,
                project_id=project_id,
                query=query,
            )
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
