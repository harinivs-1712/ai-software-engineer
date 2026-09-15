from services.web_search_service import perform_web_search
from tools.base import BaseTool


class WebSearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search external web sources for current real-time events, current office holders, "
            "recent news, up-to-date facts, latest software releases, or external technical documentation."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query string to look up on the web "
                        "(e.g. 'FastAPI background tasks documentation')."
                    ),
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs):
        query = kwargs.get("query")

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

        try:
            return perform_web_search(query=query)
        except Exception as error:
            return {
                "success": False,
                "error": f"Web search failed: {str(error)}",
            }
