# Koleo MCP Server — Design Document

**Date:** 2026-02-27  
**Status:** Approved

---

## Goal

Build a Python MCP (Model Context Protocol) server that exposes the Koleo train timetable API as callable tools for AI assistants like Claude. The server allows querying Polish train schedules, connections, station boards, and seat availability.

---

## Decisions Made

| Question | Decision |
|---|---|
| Language | Python 3.12 |
| API access | Import `koleo-cli` as pip package, reuse `KoleoAPI` directly |
| Tool scope | All public tools + auth-required tools (realtime, seat maps) |
| Auth | Config file at `~/.config/koleo-mcp/config.json` |
| Response format | Both: structured JSON `data` + human-readable `summary` + `koleo_url` |
| Architecture | Modular: `tools/` modules + `formatters/` layer |

---

## Architecture

```
koleo-mcp/
├── server.py              # MCP server entry point, tool registration
├── client.py              # Shared KoleoAPI factory (singleton)
├── config.py              # Config loading (~/.config/koleo-mcp/config.json)
├── errors.py              # Centralized error handling
├── tools/
│   ├── stations.py        # search_stations, get_station_info
│   ├── board.py           # get_departures, get_arrivals, get_all_trains
│   ├── connections.py     # search_connections
│   ├── trains.py          # get_train_route, get_train_by_id, get_train_calendar
│   ├── seats.py           # get_seat_stats, get_seat_availability, get_brands, get_carriers
│   └── realtime.py        # get_realtime_timetable (auth required)
├── formatters/
│   ├── board.py           # departure/arrival board summaries
│   ├── connections.py     # connection search summaries
│   └── trains.py          # train route summaries
├── docs/
│   └── plans/
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Tools (14 total)

| Tool | Module | Auth? | Key Parameters |
|---|---|---|---|
| `search_stations` | stations | No | `query`, `type?`, `country?` |
| `get_station_info` | stations | No | `station` (name or slug) |
| `get_departures` | board | No | `station`, `date?` (ISO) |
| `get_arrivals` | board | No | `station`, `date?` (ISO) |
| `get_all_trains` | board | No | `station`, `date?` (ISO) |
| `search_connections` | connections | No | `start`, `end`, `date?`, `brands?`, `direct?`, `include_prices?`, `length?` |
| `get_train_route` | trains | No | `brand`, `train_number`, `date?`, `closest?` |
| `get_train_by_id` | trains | No | `train_id` (int) |
| `get_train_calendar` | trains | No | `brand`, `train_number` |
| `get_realtime_timetable` | realtime | **Yes** | `train_id`, `operating_day?` |
| `get_seat_stats` | seats | No | `brand`, `train_number`, `date?`, `stations?` |
| `get_seat_availability` | seats | No | `connection_id`, `train_nr`, `place_type` |
| `get_brands` | seats | No | — |
| `get_carriers` | seats | No | — |

---

## Response Format

Every tool returns a JSON object:

```json
{
  "data": { "...": "structured API response (typed dicts from koleo-cli)" },
  "summary": "Human-readable one-paragraph description of the result",
  "koleo_url": "https://koleo.pl/... (deep link to relevant page, empty string if N/A)"
}
```

On error:
```json
{
  "data": null,
  "summary": "Error description",
  "error": "not_found | auth_required | unknown",
  "koleo_url": ""
}
```

---

## Auth Config

File: `~/.config/koleo-mcp/config.json`  
Override path: `KOLEO_MCP_CONFIG` environment variable

```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

Auth-required tools gracefully return an `auth_required` error if credentials are missing.

---

## Dependencies

- `mcp[cli]>=1.0` — official Python MCP SDK
- `koleo-cli` — provides `KoleoAPI` and all typed response classes
- `aiohttp` — HTTP client (transitive via koleo-cli)
- `orjson` — fast JSON (transitive via koleo-cli)

---

## Claude Desktop Integration

```json
{
  "mcpServers": {
    "koleo": {
      "command": "python",
      "args": ["/path/to/koleo-mcp/server.py"]
    }
  }
}
```
