from tools.base import BaseTool
from services.file_system_service import (
    list_files_service,
    read_file_service,
    search_files_service,
    get_file_info_service,
)


class ListFilesTool(BaseTool):

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return (
            "List direct files and subdirectories under a directory path within the project."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": (
                        "Subdirectory path within the project to list. "
                        "Leave empty or use '.' for root directory."
                    ),
                },
                "project_id": {
                    "type": "integer",
                    "description": "Optional project ID.",
                },
            },
        }

    def execute(self, **kwargs):
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("project_id") or kwargs.get("_project_id")
        directory = kwargs.get("directory", "")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "Active user and project context are required for file system tools.",
            }

        return list_files_service(
            db=db,
            user_id=user_id,
            project_id=project_id,
            directory=directory,
        )


class ReadFileTool(BaseTool):

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read file content from the project with optional line range slicing (start_line, end_line)."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path within the project (e.g. 'src/main.py').",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-indexed).",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Line number to stop reading at (inclusive).",
                },
                "project_id": {
                    "type": "integer",
                    "description": "Optional project ID.",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs):
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("project_id") or kwargs.get("_project_id")
        path = kwargs.get("path")
        start_line = kwargs.get("start_line", 1)
        end_line = kwargs.get("end_line")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "Active user and project context are required for file system tools.",
            }

        return read_file_service(
            db=db,
            user_id=user_id,
            project_id=project_id,
            path=path,
            start_line=start_line,
            end_line=end_line,
        )


class SearchFilesTool(BaseTool):

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return (
            "Search for a text string or code snippet across all project files."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text or code query to search for in project files.",
                },
                "path_prefix": {
                    "type": "string",
                    "description": "Optional directory path prefix to limit search scope.",
                },
                "project_id": {
                    "type": "integer",
                    "description": "Optional project ID.",
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs):
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("project_id") or kwargs.get("_project_id")
        query = kwargs.get("query")
        path_prefix = kwargs.get("path_prefix", "")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "Active user and project context are required for file system tools.",
            }

        return search_files_service(
            db=db,
            user_id=user_id,
            project_id=project_id,
            query=query,
            path_prefix=path_prefix,
        )


class GetFileInfoTool(BaseTool):

    @property
    def name(self) -> str:
        return "get_file_info"

    @property
    def description(self) -> str:
        return (
            "Retrieve file metadata (size, line count, extension) for a specific file in the project."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path within the project.",
                },
                "project_id": {
                    "type": "integer",
                    "description": "Optional project ID.",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs):
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("project_id") or kwargs.get("_project_id")
        path = kwargs.get("path")

        if not db or not user_id or not project_id:
            return {
                "success": False,
                "error": "Active user and project context are required for file system tools.",
            }

        return get_file_info_service(
            db=db,
            user_id=user_id,
            project_id=project_id,
            path=path,
        )
