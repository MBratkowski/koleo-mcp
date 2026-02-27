# Koleo MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python MCP server exposing 14 Koleo train timetable tools with structured JSON + human-readable summaries.

**Architecture:** Modular server (`server.py`) using the official `mcp` Python SDK. Tool logic in `tools/` modules; formatting in `formatters/`. Imports `koleo-cli` package for `KoleoAPI` and typed responses.

**Tech Stack:** Python 3.12, `mcp[cli]>=1.0`, `koleo-cli` (pip), `aiohttp`, `orjson`

**Design doc:** `docs/plans/2026-02-27-koleo-mcp-design.md`

---

### Task 1: Project scaffold and dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `server.py`
- Create: `config.py`
- Create: `.gitignore`

**Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "koleo-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mcp[cli]>=1.0",
    "koleo-cli",
    "aiohttp",
    "orjson",
]

[project.scripts]
koleo-mcp = "server:main"

[tool.ruff]
line-length = 120
target-version = "py312"
```

**Step 2: Create `requirements.txt`**

```
mcp[cli]>=1.0
koleo-cli
aiohttp
orjson
```

**Step 3: Create `config.py`**

```python
import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "koleo-mcp" / "config.json"


def load_config(path: Path | None = None) -> dict:
    p = path or Path(os.environ.get("KOLEO_MCP_CONFIG", str(DEFAULT_CONFIG_PATH)))
    if p.exists():
        return json.loads(p.read_text())
    return {}
```

**Step 4: Create stub `server.py`**

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("koleo")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
```

**Step 5: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/
.env
.worktrees/
```

**Step 6: Install and verify server starts**

Run: `pip install -e . && python server.py --help`
Expected: No errors, MCP server help text shown

**Step 7: Commit**

```bash
git add pyproject.toml requirements.txt server.py config.py .gitignore
git commit -m "feat: scaffold koleo-mcp project with mcp SDK"
```

---

### Task 2: Shared API client factory + error handling

**Files:**
- Create: `client.py`
- Create: `errors.py`

**Step 1: Create `client.py`**

```python
from koleo.api.client import KoleoAPI
from config import load_config

_client: KoleoAPI | None = None


def get_client() -> KoleoAPI:
    global _client
    if _client is None:
        config = load_config()
        # KoleoAPI auth dict uses cookie key-value pairs; public API works without auth
        _client = KoleoAPI()
    return _client


def reset_client() -> None:
    """Force re-creation of client (useful after config changes)."""
    global _client
    _client = None
```

**Step 2: Create `errors.py`**

```python
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
```

**Step 3: Commit**

```bash
git add client.py errors.py
git commit -m "feat: add shared KoleoAPI client factory and error handler"
```

---

### Task 3: Formatters

**Files:**
- Create: `formatters/__init__.py`
- Create: `formatters/board.py`
- Create: `formatters/connections.py`
- Create: `formatters/trains.py`

**Step 1: Create `formatters/__init__.py`** (empty)

**Step 2: Create `formatters/board.py`**

```python
from datetime import datetime
from koleo.api.types import TrainOnStationInfo


def format_train_on_station(train: TrainOnStationInfo, type: str = "departure") -> str:
    time_key = "departure" if type == "departure" else "arrival"
    time_val = train.get(time_key, "")
    time_str = time_val[:16] if time_val else "??:??"
    name = train.get("train_full_name", "")
    first_station = train["stations"][0]["name"] if train.get("stations") else ""
    platform = train.get("platform", "")
    track = train.get("track", "")
    pos = ""
    if platform:
        pos += f" pl.{platform}"
    if track:
        pos += f"/{track}"
    return f"{time_str}  {name}  ({first_station}){pos}"


def summarize_board(trains: list[TrainOnStationInfo], station_name: str, date_str: str, type: str) -> str:
    label = "Departures" if type == "departure" else "Arrivals"
    lines = [f"{station_name} — {label} on {date_str}:"]
    lines += [format_train_on_station(t, type) for t in trains[:20]]
    if len(trains) > 20:
        lines.append(f"  ... and {len(trains) - 20} more")
    if not trains:
        lines.append("  No trains found for this time.")
    return "\n".join(lines)
```

**Step 3: Create `formatters/connections.py`**

```python
from koleo.api.types import V3ConnectionResult


def format_connection(conn: V3ConnectionResult, price: dict | None = None) -> str:
    dep = (conn.get("departure") or "")[:16]
    arr = (conn.get("arrival") or "")[:16]
    duration = conn.get("duration", 0)
    changes = conn.get("changes", 0)
    legs = conn.get("legs", [])
    train_names = [
        leg.get("train_full_name", "")
        for leg in legs
        if leg.get("leg_type") == "train_leg"
    ]
    price_str = f"  [{price['price']}]" if price else ""
    change_str = f"{changes} change(s)" if changes else "direct"
    return f"{dep} → {arr}  {duration}min  {change_str}  via {', '.join(train_names)}{price_str}"


def summarize_connections(
    connections: list[V3ConnectionResult],
    start_name: str,
    end_name: str,
    prices: dict[str, dict],
) -> str:
    lines = [f"Connections {start_name} → {end_name}:"]
    for c in connections:
        lines.append("  " + format_connection(c, prices.get(c.get("uuid", ""))))
    if not connections:
        lines.append("  No connections found.")
    return "\n".join(lines)
```

**Step 4: Create `formatters/trains.py`**

```python
from koleo.api.types import TrainStop, TrainDetail


def _format_time(t: dict | str | None) -> str:
    if not t:
        return "     "
    if isinstance(t, dict):
        return f"{t.get('hour', 0):02d}:{t.get('minute', 0):02d}"
    # ISO string
    return str(t)[11:16]


def format_stop(stop: TrainStop) -> str:
    arr = _format_time(stop.get("arrival"))
    dep = _format_time(stop.get("departure"))
    name = stop.get("station_display_name") or stop.get("station_name", "?")
    platform = stop.get("platform", "")
    pos = f" pl.{platform}" if platform else ""
    dist_km = stop.get("distance", 0) / 1000
    return f"{dist_km:>6.1f}km  {arr} / {dep}  {name}{pos}"


def summarize_train_route(train: TrainDetail, stops: list[TrainStop]) -> str:
    lines = [
        f"{train.get('train_full_name', '?')}",
        f"  Runs: {train.get('run_desc', 'N/A')}",
        f"  {len(stops)} stops:",
    ]
    first_dist = stops[0]["distance"] if stops else 0
    for stop in stops:
        stop = dict(stop)
        stop["distance"] = stop["distance"] - first_dist
        lines.append("  " + format_stop(stop))
    return "\n".join(lines)
```

**Step 5: Commit**

```bash
git add formatters/
git commit -m "feat: add board, connections, trains formatters"
```

---

### Task 4: Station tools

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/stations.py`
- Modify: `server.py`

**Step 1: Create `tools/__init__.py`** (empty)

**Step 2: Create `tools/stations.py`**

```python
import json
from koleo.utils import name_to_slug
from client import get_client
from errors import handle_tool_error


async def search_stations(query: str, type: str | None = None, country: str | None = None) -> dict:
    try:
        client = get_client()
        results = await client.find_station(query)
        if type:
            results = [s for s in results if s.get("type", "").lower() == type.lower()]
        if country:
            # find_station doesn't return country; use get_stations for filtering
            all_stations = await client.get_stations()
            country_ids = {s["id"] for s in all_stations if s.get("country", "").lower() == country.lower()}
            results = [s for s in results if s["id"] in country_ids]
        summary_lines = [
            f"  {s['name']} (id={s['id']}, type={s.get('type', '')}, slug={s['name_slug']})"
            for s in results[:15]
        ]
        return {
            "data": results,
            "summary": f"Found {len(results)} station(s) matching '{query}':\n" + "\n".join(summary_lines),
            "koleo_url": f"https://koleo.pl/ls?q={query}",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_station_info(station: str) -> dict:
    try:
        client = get_client()
        slug = station if ("-" in station and station.islower()) else name_to_slug(station)
        st, info = await __import__("asyncio").gather(
            client.get_station_by_slug(slug),
            client.get_station_info_by_slug(slug),
        )
        features = [f["name"] for f in info.get("features", []) if f.get("available")]
        address = info.get("address", {}).get("full", "N/A")
        hours = info.get("opening_hours", [])
        hours_str = ", ".join(f"day{h['day']}: {h['open']}-{h['close']}" for h in hours[:3]) if hours else "N/A"
        summary = (
            f"{st['name']} (id={st['id']}, slug={st['name_slug']})\n"
            f"  Address: {address}\n"
            f"  Opening hours: {hours_str}\n"
            f"  Features: {', '.join(features) or 'none listed'}"
        )
        return {
            "data": {"station": st, "info": info},
            "summary": summary,
            "koleo_url": f"https://koleo.pl/dworzec-pkp/{slug}",
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 3: Register tools in `server.py`**

```python
import json
from mcp.server.fastmcp import FastMCP
from tools.stations import search_stations, get_station_info

mcp = FastMCP("koleo")


@mcp.tool(description="Search for train stations by name. Returns station IDs, slugs, and types.")
async def tool_search_stations(
    query: str,
    type: str | None = None,
    country: str | None = None,
) -> str:
    """
    Args:
        query: Station name to search for (e.g. 'Kraków', 'Warszawa')
        type: Optional filter by type: 'rail', 'bus', 'group'
        country: Optional filter by country code: 'pl', 'de', etc.
    """
    return json.dumps(await search_stations(query, type, country), ensure_ascii=False)


@mcp.tool(description="Get detailed info about a station: address, opening hours, available facilities.")
async def tool_get_station_info(station: str) -> str:
    """
    Args:
        station: Station name (e.g. 'Kraków Główny') or slug (e.g. 'krakow-glowny')
    """
    return json.dumps(await get_station_info(station), ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
```

**Step 4: Manual smoke test**

Run: `python -c "import asyncio; from tools.stations import search_stations; import json; print(json.dumps(asyncio.run(search_stations('Kraków')), ensure_ascii=False, indent=2))"`

Expected: JSON with `data`, `summary`, `koleo_url` keys, list of matching stations

**Step 5: Commit**

```bash
git add tools/ server.py
git commit -m "feat: add search_stations and get_station_info tools"
```

---

### Task 5: Station board tools

**Files:**
- Create: `tools/board.py`
- Modify: `server.py`

**Step 1: Create `tools/board.py`**

```python
from datetime import datetime
from asyncio import gather
from koleo.utils import name_to_slug
from client import get_client
from errors import handle_tool_error
from formatters.board import summarize_board


async def _resolve_station(station: str):
    client = get_client()
    # If it looks like a slug already, use directly; otherwise convert
    slug = station if ("-" in station and station.islower()) else name_to_slug(station)
    return await client.get_station_by_slug(slug)


async def get_departures(station: str, date: str | None = None) -> dict:
    try:
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()
        st = await _resolve_station(station)
        trains = await client.get_departures(st["id"], dt)
        trains = [t for t in trains if (t.get("departure") or "") >= dt.isoformat()[:16]]
        return {
            "data": trains,
            "summary": summarize_board(trains, st["name"], dt.strftime("%Y-%m-%d %H:%M"), "departure"),
            "koleo_url": f"https://koleo.pl/dworzec-pkp/{st['name_slug']}/odjazdy/{dt.strftime('%Y-%m-%d')}",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_arrivals(station: str, date: str | None = None) -> dict:
    try:
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()
        st = await _resolve_station(station)
        trains = await client.get_arrivals(st["id"], dt)
        trains = [t for t in trains if (t.get("arrival") or "") >= dt.isoformat()[:16]]
        return {
            "data": trains,
            "summary": summarize_board(trains, st["name"], dt.strftime("%Y-%m-%d %H:%M"), "arrival"),
            "koleo_url": f"https://koleo.pl/dworzec-pkp/{st['name_slug']}/przyjazdy/{dt.strftime('%Y-%m-%d')}",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_all_trains(station: str, date: str | None = None) -> dict:
    try:
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()
        st = await _resolve_station(station)
        departures, arrivals = await gather(
            client.get_departures(st["id"], dt),
            client.get_arrivals(st["id"], dt),
        )
        dt_iso = dt.isoformat()[:16]
        combined = sorted(
            [(t, "departure") for t in departures if (t.get("departure") or "") >= dt_iso]
            + [(t, "arrival") for t in arrivals if (t.get("arrival") or "") >= dt_iso],
            key=lambda x: (x[0].get(x[1]) or ""),
        )
        summary_lines = []
        for t, typ in combined[:20]:
            time = (t.get(typ) or "")[:16]
            label = "DEP" if typ == "departure" else "ARR"
            name = t.get("train_full_name", "")
            first = t["stations"][0]["name"] if t.get("stations") else ""
            summary_lines.append(f"  {label} {time}  {name}  ({first})")
        if len(combined) > 20:
            summary_lines.append(f"  ... and {len(combined) - 20} more")
        return {
            "data": [{"train": t, "type": typ} for t, typ in combined],
            "summary": f"{st['name']} — all trains on {dt.strftime('%Y-%m-%d %H:%M')}:\n" + "\n".join(summary_lines),
            "koleo_url": f"https://koleo.pl/dworzec-pkp/{st['name_slug']}/odjazdy/{dt.strftime('%Y-%m-%d')}",
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 2: Add 3 tool registrations to `server.py`**

```python
from tools.board import get_departures, get_arrivals, get_all_trains

@mcp.tool(description="Get upcoming train departures from a station.")
async def tool_get_departures(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name (e.g. 'Kraków Główny') or slug
        date: ISO datetime (e.g. '2026-02-27T14:00'). Defaults to now.
    """
    return json.dumps(await get_departures(station, date), ensure_ascii=False)


@mcp.tool(description="Get upcoming train arrivals at a station.")
async def tool_get_arrivals(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name or slug
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_arrivals(station, date), ensure_ascii=False)


@mcp.tool(description="Get all trains (both departures and arrivals) at a station, sorted by time.")
async def tool_get_all_trains(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name or slug
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_all_trains(station, date), ensure_ascii=False)
```

**Step 3: Smoke test**

Run: `python -c "import asyncio; from tools.board import get_departures; import json; print(json.dumps(asyncio.run(get_departures('Kraków Główny')), ensure_ascii=False, indent=2)[:500])"`

Expected: JSON with departure list

**Step 4: Commit**

```bash
git add tools/board.py server.py
git commit -m "feat: add get_departures, get_arrivals, get_all_trains tools"
```

---

### Task 6: Connection search tool

**Files:**
- Create: `tools/connections.py`
- Modify: `server.py`

**Step 1: Create `tools/connections.py`**

```python
from datetime import datetime, timedelta
from asyncio import gather
from koleo.utils import name_to_slug, koleo_time_to_dt
from client import get_client
from errors import handle_tool_error
from formatters.connections import summarize_connections


async def search_connections(
    start: str,
    end: str,
    date: str | None = None,
    brands: list[str] | None = None,
    direct: bool = False,
    include_prices: bool = False,
    length: int = 5,
) -> dict:
    try:
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()

        start_slug = start if ("-" in start and start.islower()) else name_to_slug(start)
        end_slug = end if ("-" in end and end.islower()) else name_to_slug(end)

        start_station, end_station, api_brands = await gather(
            client.get_station_by_slug(start_slug),
            client.get_station_by_slug(end_slug),
            client.get_brands(),
        )

        if brands:
            brands_lower = [b.lower() for b in brands]
            brand_ids = [
                b["id"]
                for b in api_brands
                if b["name"].lower() in brands_lower or b["logo_text"].lower() in brands_lower
            ]
        else:
            brand_ids = [b["id"] for b in api_brands]

        results = []
        fetch_date = dt
        while len(results) < length:
            connections = await client.v3_connection_search(
                start_station["id"], end_station["id"], brand_ids, fetch_date, direct
            )
            if not connections:
                break
            results.extend(connections)
            fetch_date = koleo_time_to_dt(connections[-1]["departure"]) + timedelta(seconds=1801)

        results = results[:length]

        prices: dict = {}
        if include_prices and results:
            price_results = await gather(*(client.v3_get_price(c["uuid"]) for c in results))
            prices = {c["uuid"]: p for c, p in zip(results, price_results) if p}

        link = (
            f"https://koleo.pl/rozklad-pkp/{start_slug}/{end_slug}"
            f"/{dt.strftime('%d-%m-%Y_%H:%M')}"
            f"/{'direct' if direct else 'all'}/all"
        )
        return {
            "data": [{"connection": c, "price": prices.get(c["uuid"])} for c in results],
            "summary": summarize_connections(results, start_station["name"], end_station["name"], prices),
            "koleo_url": link,
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 2: Add tool registration to `server.py`**

```python
from tools.connections import search_connections

@mcp.tool(description="Search for train connections between two stations.")
async def tool_search_connections(
    start: str,
    end: str,
    date: str | None = None,
    brands: list[str] | None = None,
    direct: bool = False,
    include_prices: bool = False,
    length: int = 5,
) -> str:
    """
    Args:
        start: Starting station name (e.g. 'Kraków') or slug
        end: Destination station name or slug
        date: ISO datetime for departure after. Defaults to now.
        brands: Optional list of brand codes to filter (e.g. ['IC', 'REG'])
        direct: If True, only return direct trains (no changes)
        include_prices: If True, fetch prices for each connection
        length: Maximum number of connections to return (default 5)
    """
    return json.dumps(
        await search_connections(start, end, date, brands, direct, include_prices, length),
        ensure_ascii=False,
    )
```

**Step 3: Smoke test**

Run: `python -c "import asyncio; from tools.connections import search_connections; import json; r = asyncio.run(search_connections('Kraków', 'Warszawa', length=3)); print(r['summary'])"`

Expected: Summary showing 3 connections with departure/arrival times

**Step 4: Commit**

```bash
git add tools/connections.py server.py
git commit -m "feat: add search_connections tool with V3 API"
```

---

### Task 7: Train info tools

**Files:**
- Create: `tools/trains.py`
- Modify: `server.py`

**Step 1: Create `tools/trains.py`**

```python
from datetime import datetime
from client import get_client
from errors import handle_tool_error
from formatters.trains import summarize_train_route


async def get_train_route(
    brand: str,
    train_number: str,
    date: str | None = None,
    closest: bool = False,
) -> dict:
    try:
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()
        brand_upper = brand.upper()
        nr = int(train_number) if train_number.isdigit() else 0

        calendars = await client.get_train_calendars(brand_upper, nr)
        cals = calendars.get("train_calendars", [])
        if not cals:
            return {"data": None, "summary": f"No train found for {brand} {train_number}", "koleo_url": ""}

        cal = cals[0]
        date_str = dt.strftime("%Y-%m-%d")

        if closest or date_str not in cal.get("date_train_map", {}):
            future = sorted(d for d in cal.get("dates", []) if d >= date_str)
            date_str = future[0] if future else sorted(cal.get("dates", []))[-1]

        train_id = cal.get("date_train_map", {}).get(date_str)
        if not train_id:
            return {
                "data": None,
                "summary": f"Train {brand} {train_number} does not run on {date_str}",
                "koleo_url": "",
            }

        detail = await client.get_train(train_id)
        return {
            "data": detail,
            "summary": summarize_train_route(detail["train"], detail["stops"]),
            "koleo_url": f"https://koleo.pl/pl/trains/{train_id}",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_train_by_id(train_id: int) -> dict:
    try:
        client = get_client()
        detail = await client.get_train(train_id)
        return {
            "data": detail,
            "summary": summarize_train_route(detail["train"], detail["stops"]),
            "koleo_url": f"https://koleo.pl/pl/trains/{train_id}",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_train_calendar(brand: str, train_number: str) -> dict:
    try:
        client = get_client()
        nr = int(train_number) if train_number.isdigit() else 0
        calendars = await client.get_train_calendars(brand.upper(), nr)
        cals = calendars.get("train_calendars", [])
        if not cals:
            return {"data": [], "summary": f"No calendar found for {brand} {train_number}", "koleo_url": ""}
        cal = cals[0]
        dates = cal.get("dates", [])
        today = datetime.now().strftime("%Y-%m-%d")
        next_date = next((d for d in sorted(dates) if d >= today), None)
        return {
            "data": cals,
            "summary": (
                f"{cal.get('train_name', '?')} ({brand} {train_number}) "
                f"runs on {len(dates)} day(s). "
                f"Next: {next_date or 'no future dates found'}."
            ),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 2: Add 3 tool registrations to `server.py`**

```python
from tools.trains import get_train_route, get_train_by_id, get_train_calendar

@mcp.tool(description="Get the full route and stop schedule for a train by brand and number.")
async def tool_get_train_route(
    brand: str,
    train_number: str,
    date: str | None = None,
    closest: bool = False,
) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG', 'EIC', 'KM')
        train_number: Train number as string (e.g. '1106', '10417')
        date: ISO date/datetime. Defaults to today.
        closest: If True, find the closest running date if train doesn't run on given date.
    """
    return json.dumps(await get_train_route(brand, train_number, date, closest), ensure_ascii=False)


@mcp.tool(description="Get a train's route and stops by its internal Koleo ID.")
async def tool_get_train_by_id(train_id: int) -> str:
    """
    Args:
        train_id: Koleo internal train ID (integer)
    """
    return json.dumps(await get_train_by_id(train_id), ensure_ascii=False)


@mcp.tool(description="Get all dates when a specific train runs (operating calendar).")
async def tool_get_train_calendar(brand: str, train_number: str) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG')
        train_number: Train number as string
    """
    return json.dumps(await get_train_calendar(brand, train_number), ensure_ascii=False)
```

**Step 3: Smoke test**

Run: `python -c "import asyncio; from tools.trains import get_train_calendar; import json; r = asyncio.run(get_train_calendar('IC', '1106')); print(r['summary'])"`

**Step 4: Commit**

```bash
git add tools/trains.py server.py
git commit -m "feat: add get_train_route, get_train_by_id, get_train_calendar tools"
```

---

### Task 8: Seat & reference tools

**Files:**
- Create: `tools/seats.py`
- Modify: `server.py`

**Step 1: Create `tools/seats.py`**

```python
from datetime import datetime
from asyncio import gather
from koleo.utils import name_to_slug
from client import get_client
from errors import handle_tool_error


async def get_seat_stats(
    brand: str,
    train_number: str,
    date: str | None = None,
    stations: list[str] | None = None,
) -> dict:
    """Get seat occupancy statistics for a train on a connection."""
    try:
        if not stations or len(stations) != 2:
            return {
                "data": None,
                "summary": "stations parameter is required: provide [start_station, end_station]",
                "error": "invalid_params",
                "koleo_url": "",
            }
        client = get_client()
        dt = datetime.fromisoformat(date) if date else datetime.now()

        start_slug = name_to_slug(stations[0])
        end_slug = name_to_slug(stations[1])
        start_st, end_st, api_brands = await gather(
            client.get_station_by_slug(start_slug),
            client.get_station_by_slug(end_slug),
            client.get_brands(),
        )

        brand_upper = brand.upper()
        brand_obj = next(
            (b for b in api_brands if b["name"].upper() == brand_upper or b["logo_text"].upper() == brand_upper),
            None,
        )
        brand_ids = [brand_obj["id"]] if brand_obj else [b["id"] for b in api_brands]
        nr = int(train_number) if train_number.isdigit() else None

        connections = await client.v3_connection_search(start_st["id"], end_st["id"], brand_ids, dt)
        conn = next(
            (
                c
                for c in connections
                for leg in c.get("legs", [])
                if leg.get("leg_type") == "train_leg" and (nr is None or leg.get("train_nr") == nr)
            ),
            None,
        )
        if not conn:
            return {"data": None, "summary": f"Train {brand} {train_number} not found on this connection", "koleo_url": ""}

        connection_id = await client.v3_get_connection_id(conn["uuid"])
        detail = await client.get_connection(connection_id)
        train = detail["trains"][0]
        availability = await client.get_seats_availability(connection_id, train["train_nr"], 1)

        seats = availability.get("seats", [])
        total = len(seats)
        free = sum(1 for s in seats if s["state"] == "FREE")
        reserved = sum(1 for s in seats if s["state"] == "RESERVED")
        blocked = total - free - reserved

        return {
            "data": availability,
            "summary": (
                f"{brand} {train_number} on {start_st['name']} → {end_st['name']}:\n"
                f"  {free}/{total} seats free, {reserved} reserved, {blocked} blocked"
            ),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_seat_availability(connection_id: int, train_nr: int, place_type: int) -> dict:
    """Get raw seat availability for a specific connection/train/place_type combination."""
    try:
        client = get_client()
        availability = await client.get_seats_availability(connection_id, train_nr, place_type)
        seats = availability.get("seats", [])
        total = len(seats)
        free = sum(1 for s in seats if s["state"] == "FREE")
        return {
            "data": availability,
            "summary": f"{free}/{total} seats free for connection {connection_id}, train {train_nr}, type {place_type}",
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_brands() -> dict:
    try:
        client = get_client()
        brands = await client.get_brands()
        lines = [f"  {b['logo_text']:6} ({b['name']})" for b in brands]
        return {
            "data": brands,
            "summary": "Available train brands:\n" + "\n".join(lines),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)


async def get_carriers() -> dict:
    try:
        client = get_client()
        carriers = await client.get_carriers()
        lines = [f"  {c['short_name']:6} — {c['name']}" for c in carriers]
        return {
            "data": carriers,
            "summary": "Train carriers:\n" + "\n".join(lines),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 2: Add 4 tool registrations to `server.py`**

```python
from tools.seats import get_seat_stats, get_seat_availability, get_brands, get_carriers

@mcp.tool(description="Check seat occupancy statistics for a train on a given route segment.")
async def tool_get_seat_stats(
    brand: str,
    train_number: str,
    stations: list[str],
    date: str | None = None,
) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG')
        train_number: Train number as string
        stations: List of exactly 2 stations: [start_station, end_station]
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_seat_stats(brand, train_number, date, stations), ensure_ascii=False)


@mcp.tool(description="Get raw seat availability for a connection by connection_id, train_nr, and place_type.")
async def tool_get_seat_availability(connection_id: int, train_nr: int, place_type: int) -> str:
    """
    Args:
        connection_id: Koleo connection ID (integer)
        train_nr: Train number (integer)
        place_type: Seat/place type ID (integer, e.g. 1 for standard)
    """
    return json.dumps(await get_seat_availability(connection_id, train_nr, place_type), ensure_ascii=False)


@mcp.tool(description="List all available train brands/operators (IC, REG, EIC, KM, etc.).")
async def tool_get_brands() -> str:
    return json.dumps(await get_brands(), ensure_ascii=False)


@mcp.tool(description="List all train carriers (PKP Intercity, POLREGIO, etc.).")
async def tool_get_carriers() -> str:
    return json.dumps(await get_carriers(), ensure_ascii=False)
```

**Step 3: Smoke test**

Run: `python -c "import asyncio; from tools.seats import get_brands; import json; print(asyncio.run(get_brands())['summary'])"`

Expected: List of brand codes and names

**Step 4: Commit**

```bash
git add tools/seats.py server.py
git commit -m "feat: add seat stats, seat availability, brands, carriers tools"
```

---

### Task 9: Auth-required realtime tool

**Files:**
- Create: `tools/realtime.py`
- Modify: `server.py`

**Step 1: Create `tools/realtime.py`**

```python
from datetime import datetime
from config import load_config
from client import get_client
from errors import handle_tool_error


async def get_realtime_timetable(train_id: int, operating_day: str | None = None) -> dict:
    """Get realtime timetable for a train (requires authentication)."""
    config = load_config()
    if "email" not in config or "password" not in config:
        return {
            "data": None,
            "summary": (
                "This tool requires authentication. "
                "Create ~/.config/koleo-mcp/config.json with:\n"
                '  {"email": "your@email.com", "password": "yourpassword"}'
            ),
            "error": "auth_required",
            "koleo_url": "",
        }
    try:
        client = get_client()
        day = datetime.fromisoformat(operating_day) if operating_day else datetime.now()

        timetable = await client.realtime_train_timetable(train_id, day)
        stops = timetable.get("stops", [])

        def fmt_time(t: str | None) -> str:
            return t[11:16] if t else "     "

        summary_lines = []
        for s in stops[:15]:
            actual = fmt_time(s.get("actual_departure") or s.get("actual_arrival"))
            aimed = fmt_time(s.get("aimed_departure") or s.get("aimed_arrival") or s.get("departure"))
            delayed = " (DELAYED)" if actual and actual != aimed else ""
            summary_lines.append(f"  {aimed} → {actual}  station_id={s['station_id']}{delayed}")

        if len(stops) > 15:
            summary_lines.append(f"  ... and {len(stops) - 15} more stops")

        return {
            "data": timetable,
            "summary": (
                f"Realtime timetable: {timetable.get('train_full_name', train_id)} "
                f"on {day.date()}\n" + "\n".join(summary_lines)
            ),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)
```

**Step 2: Add tool registration to `server.py`**

```python
from tools.realtime import get_realtime_timetable

@mcp.tool(description="Get realtime timetable for a train, including actual vs scheduled times. Requires authentication in config.")
async def tool_get_realtime_timetable(train_id: int, operating_day: str | None = None) -> str:
    """
    Args:
        train_id: Koleo internal train ID (integer)
        operating_day: ISO date (e.g. '2026-02-27'). Defaults to today.
    """
    return json.dumps(await get_realtime_timetable(train_id, operating_day), ensure_ascii=False)
```

**Step 3: Test auth error path**

Run: `python -c "import asyncio; from tools.realtime import get_realtime_timetable; import json; r = asyncio.run(get_realtime_timetable(12345)); print(r['summary'])"`

Expected: Auth required message (if no config file) OR realtime data (if config exists)

**Step 4: Commit**

```bash
git add tools/realtime.py server.py
git commit -m "feat: add get_realtime_timetable tool with graceful auth check"
```

---

### Task 10: Final integration test + README

**Files:**
- Create: `README.md`

**Step 1: Run full server via MCP dev inspector**

Run: `mcp dev server.py`

Open the inspector UI and test each of these tools manually:
- `tool_search_stations` with query `"Kraków"`
- `tool_get_departures` with station `"Kraków Główny"`
- `tool_search_connections` with start `"Kraków"`, end `"Warszawa"`, length `3`
- `tool_get_brands`
- `tool_get_realtime_timetable` with any train_id (expect auth error or data)

Expected: All tools return valid JSON with `data`, `summary`, `koleo_url` keys

**Step 2: Create `README.md`**

```markdown
# koleo-mcp

MCP server for the [Koleo](https://koleo.pl) Polish train timetable API. Exposes 14 tools for use with Claude and other MCP-compatible AI assistants.

## Installation

\```bash
pip install -e .
\```

Or install dependencies directly:
\```bash
pip install -r requirements.txt
\```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

\```json
{
  "mcpServers": {
    "koleo": {
      "command": "python",
      "args": ["/absolute/path/to/koleo-mcp/server.py"]
    }
  }
}
\```

## Authentication (Optional)

Some tools (realtime timetable) require a Koleo account. Create:

`~/.config/koleo-mcp/config.json`:
\```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
\```

Override config path with `KOLEO_MCP_CONFIG` env var.

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_search_stations` | Search stations by name |
| `tool_get_station_info` | Station address, hours, facilities |
| `tool_get_departures` | Departures from a station |
| `tool_get_arrivals` | Arrivals at a station |
| `tool_get_all_trains` | All trains (dep+arr) at a station |
| `tool_search_connections` | Find connections A→B |
| `tool_get_train_route` | Train route by brand+number |
| `tool_get_train_by_id` | Train route by Koleo ID |
| `tool_get_train_calendar` | Operating dates for a train |
| `tool_get_realtime_timetable` | Live timetable (auth required) |
| `tool_get_seat_stats` | Seat occupancy on a route |
| `tool_get_seat_availability` | Raw seat map by connection ID |
| `tool_get_brands` | List all train brands |
| `tool_get_carriers` | List all carriers |
```

**Step 3: Final commit**

```bash
git add README.md
git commit -m "docs: add README with installation and tool reference"
```

---

## Done

All 14 tools implemented. Server runnable via `python server.py` or `mcp dev server.py`.
