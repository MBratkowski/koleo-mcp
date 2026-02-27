# koleo-mcp

MCP server for the [Koleo](https://koleo.pl) Polish train timetable API.

It exposes 14 tools you can call from Claude Desktop (or any MCP client) to search stations, departures/arrivals, connections, train routes, seat data, and realtime timetable.

## Requirements

- Python 3.12+
- `pip`

## Quick start (copy/paste)

```bash
git clone https://github.com/MBratkowski/koleo-mcp.git
cd koleo-mcp
python3 -m pip install -e .
python3 server.py
```

If `server.py` starts without crashing, the server is ready.

## How to test the server (easy mode)

Run the MCP inspector:

```bash
mcp dev server.py
```

Then in the inspector UI call these tools:

1. `tool_search_stations` with:
   - `query`: `Krakow`
2. `tool_get_departures` with:
   - `station`: `Krakow Glowny`
3. `tool_search_connections` with:
   - `start`: `Krakow`
   - `end`: `Warszawa`
   - `length`: `3`
4. `tool_get_brands`
5. `tool_get_realtime_timetable` with:
   - `train_id`: any integer (for example `12345`)

Each tool returns JSON with at least:

- `data`
- `summary`
- `koleo_url`

On errors you also get an `error` key.

## How to use with Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "koleo": {
      "command": "python3",
      "args": ["/absolute/path/to/koleo-mcp/server.py"]
    }
  }
}
```

Replace `/absolute/path/to/koleo-mcp/server.py` with your real path.

Restart Claude Desktop.

## Authentication (optional, needed for realtime tool)

Create `~/.config/koleo-mcp/config.json`:

```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
```

You can override the config path with `KOLEO_MCP_CONFIG`.

If auth is missing, `tool_get_realtime_timetable` returns a friendly `auth_required` error.

## Available tools

| Tool | Description |
|------|-------------|
| `tool_search_stations` | Search stations by name |
| `tool_get_station_info` | Station address, opening hours, facilities |
| `tool_get_departures` | Departures from a station |
| `tool_get_arrivals` | Arrivals at a station |
| `tool_get_all_trains` | All trains (departures + arrivals) at a station |
| `tool_search_connections` | Find connections A->B |
| `tool_get_train_route` | Train route by brand + number |
| `tool_get_train_by_id` | Train route by Koleo train ID |
| `tool_get_train_calendar` | Operating dates for a train |
| `tool_get_realtime_timetable` | Live timetable (auth required) |
| `tool_get_seat_stats` | Seat occupancy stats on a route |
| `tool_get_seat_availability` | Raw seat map by connection ID |
| `tool_get_brands` | List train brands |
| `tool_get_carriers` | List carriers |

## Troubleshooting

- `ModuleNotFoundError`: run `python3 -m pip install -e .` again.
- SSL certificate errors on macOS/Python.org builds: install certificates for your Python installation and retry.
- `auth_required` for realtime tool: add `~/.config/koleo-mcp/config.json` as shown above.
