import re
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse
import requests


def _clean_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    if "uddg=" in raw_url:
        parsed = parse_qs(urlparse(raw_url).query)
        if "uddg" in parsed:
            return parsed["uddg"][0]
    if raw_url.startswith("//"):
        return "https:" + raw_url
    return raw_url


USER_AGENTS = [
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
]


def perform_web_search(query: str, max_results: int = 5) -> dict:
    """Perform a web search for the given query with resilient error handling.

    Handles:
    - Invalid queries
    - Search API / Network failures
    - Search provider timeouts
    - Search rate limiting / 429 status codes
    - Empty result sets
    - Result count capping
    """
    # 1. Invalid Query Handling
    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "query": str(query) if query is not None else "",
            "error": "Invalid query: Query must be a non-empty string.",
            "results": [],
            "count": 0,
        }

    query = query.strip()
    if len(query) > 500:
        return {
            "success": False,
            "query": query,
            "error": "Invalid query: Query exceeds maximum length of 500 characters.",
            "results": [],
            "count": 0,
        }

    # Limit result count between 1 and 10
    max_results = min(max(1, max_results), 10)
    url = "https://html.duckduckgo.com/html/"

    encountered_timeout = False
    encountered_rate_limit = False
    encountered_network_error = False

    for ua in USER_AGENTS:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            response = requests.post(
                url,
                data={"q": query},
                headers=headers,
                timeout=10,
            )

            if response.status_code in (429, 202):
                encountered_rate_limit = True
                continue

            if response.status_code >= 500:
                encountered_network_error = True
                continue

            if response.status_code != 200:
                continue

            html = response.text
            results = []

            # Extract result blocks
            blocks = re.split(r'<h2[^>]*class=["\']result__title["\']', html)
            for block in blocks[1:]:
                title_m = re.search(
                    r'<a[^>]*class=["\']result__a["\'][^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                    block,
                    re.DOTALL,
                )
                if not title_m:
                    continue

                raw_url = title_m.group(1).strip()
                raw_title = title_m.group(2).strip()

                # Ignore ad links
                if "duckduckgo.com/y.js" in raw_url or "ad_provider" in raw_url:
                    continue

                url_val = _clean_url(raw_url)
                title_val = unescape(re.sub(r"<[^>]+>", "", raw_title).strip())

                snippet_m = re.search(
                    r'<a[^>]*class=["\']result__snippet["\'][^>]*>(.*?)</a>',
                    block,
                    re.DOTALL,
                )
                if not snippet_m:
                    snippet_m = re.search(
                        r'class=["\']result__snippet[^"\']*["\'][^>]*>(.*?)</(?:a|div|span)>',
                        block,
                        re.DOTALL,
                    )

                if snippet_m:
                    raw_snippet = snippet_m.group(1).strip()
                    snippet_val = unescape(re.sub(r"<[^>]+>", "", raw_snippet).strip())
                else:
                    snippet_val = ""

                if title_val and url_val:
                    results.append(
                        {
                            "title": title_val,
                            "url": url_val,
                            "snippet": snippet_val,
                            "source": "DuckDuckGo",
                        }
                    )

                if len(results) >= max_results:
                    break

            # Return normalized result payload
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }

        except requests.exceptions.Timeout:
            encountered_timeout = True
            continue
        except requests.exceptions.RequestException:
            encountered_network_error = True
            continue
        except Exception:
            continue

    # Failure Response Resolution
    if encountered_rate_limit:
        error_msg = "Search provider rate limit exceeded. Please try again shortly."
    elif encountered_timeout:
        error_msg = "Search request timed out."
    elif encountered_network_error:
        error_msg = "Search API / Network provider unavailable."
    else:
        error_msg = "Unable to fetch web search results at this time."

    return {
        "success": False,
        "query": query,
        "error": error_msg,
        "results": [],
        "count": 0,
    }
