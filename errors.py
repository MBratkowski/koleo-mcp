from koleo.api.errors import errors as KoleoErrors


def handle_tool_error(e: Exception) -> dict:
    """Convert any exception into a standard MCP tool error response."""
    if isinstance(e, KoleoErrors.KoleoNotFound):
        return {
            "data": None,
            "summary": f"Not found: {e}",
            "error": "not_found",
            "koleo_url": "",
        }
    if isinstance(e, KoleoErrors.AuthRequired):
        return {
            "data": None,
            "summary": "Authentication required. Create ~/.config/koleo-mcp/config.json with email and password.",
            "error": "auth_required",
            "koleo_url": "",
        }
    return {
        "data": None,
        "summary": f"Error: {type(e).__name__}: {e}",
        "error": "unknown",
        "koleo_url": "",
    }
