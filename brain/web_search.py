"""
Web search module for Jarvis — fetches real-time results via DuckDuckGo.
Uses `ddgs` package (no API key needed).
"""

from duckduckgo_search import DDGS

# Keywords that trigger a web search for real-time data
REALTIME_TRIGGERS = [
    "price", "cost", "how much", "buy", "shop", "deal", "offer", "discount",
    "weather", "temperature", "forecast", "rain", "sunny", "humid",
    "news", "today", "latest", "current", "now", "right now", "live",
    "stock", "share", "market", "crypto", "bitcoin", "rupee", "dollar",
    "who is", "what is", "when is", "where is",
    "best", "top", "recommend", "suggest", "compare",
    "iphone", "samsung", "laptop", "phone", "tv", "camera", "headphone",
    "release", "launch", "update", "version",
    "score", "match", "cricket", "ipl", "football", "game",
    "election", "politics",
    "recipe", "how to make",
    "review", "specs", "specification", "feature",
]


def needs_search(query: str) -> bool:
    """Check if query needs real-time data from the web."""
    q = query.lower()
    return any(trigger in q for trigger in REALTIME_TRIGGERS)


def web_search(query: str, max_results: int = 4) -> str:
    """
    Search DuckDuckGo and return a compact context string for the AI.
    Returns empty string on failure.
    """
    try:
        d = DDGS()
        results = list(d.text(query, max_results=max_results))

        if not results:
            print(f"[Search] No results for: {query}", flush=True)
            return ""

        snippets = []
        for r in results:
            title = r.get("title", "").strip()
            body = r.get("body", "").strip()
            if body and len(body) > 20:
                snippet = f"- {title}: {body[:220]}"
                snippets.append(snippet)

        context = "\n".join(snippets)
        print(f"[Search] Found {len(snippets)} results for: {query}", flush=True)
        return context

    except Exception as e:
        print(f"[Search] Error: {e}", flush=True)
        return ""


if __name__ == "__main__":
    q = "best HP laptop under 60000 rupees 2025"
    print(f"needs_search: {needs_search(q)}")
    ctx = web_search(q)
    print("Context:\n", ctx[:600])
