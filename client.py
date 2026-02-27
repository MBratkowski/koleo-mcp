from koleo.api.client import KoleoAPI

from config import load_config

_client: KoleoAPI | None = None


def get_client() -> KoleoAPI:
    global _client
    if _client is None:
        config = load_config()
        auth = config.get("auth") if isinstance(config.get("auth"), dict) else None
        _client = KoleoAPI(auth=auth)
    return _client


def reset_client() -> None:
    """Force re-creation of client (useful after config changes)."""
    global _client
    _client = None
