from tools.base import BaseTool
from services.semantic_search_service import semantic_search


class SemanticSearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "semantic_search"

    @property
    def description(self) -> str:
        return (
            "Perform semantic code search over project files using vector embeddings (gemini-embedding-001) "
            "and AST chunk cosine similarity matching to locate relevant functions, classes, and code logic."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query or code concept to search for semantically.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top matching code chunks to return (default is 5).",
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs):
        db = kwargs.get("_db")
        user_id = kwargs.get("_user_id")
        project_id = kwargs.get("_project_id")
        query = kwargs.get("query")
        top_k = kwargs.get("top_k", 5)

        if not isinstance(query, str) or not query.strip():
            return {
                "success": False,
                "error": "Query must be a non-empty string.",
            }

        if len(query) > 500:
            return {
                "success": False,
                "error": "Query is too long. Maximum length is 500 characters.",
            }

        if not db or not user_id or not project_id:
            return semantic_search(query=query, top_k=top_k)

        try:
            return semantic_search(
                query=query,
                top_k=top_k,
                db=db,
                user_id=user_id,
                project_id=project_id,
            )
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
