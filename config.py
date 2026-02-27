import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "koleo-mcp" / "config.json"


def load_config(path: Path | None = None) -> dict:
    p = path or Path(os.environ.get("KOLEO_MCP_CONFIG", str(DEFAULT_CONFIG_PATH)))
    if p.exists():
        return json.loads(p.read_text())
    return {}
