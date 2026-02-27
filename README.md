# koleo-mcp

MCP server for the [Koleo](https://koleo.pl) Polish train timetable API. Exposes 14 tools for use with Claude and other MCP-compatible AI assistants.

## Installation

```bash
python3 -m pip install -e ../../koleo-cli
python3 -m pip install -e .
```

Or install dependencies directly:

```bash
python3 -m pip install -r requirements.txt
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

## Authentication (Optional)

Some tools (realtime timetable) require a Koleo account. Create:

`~/.config/koleo-mcp/config.json`:

```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
```

Override config path with `KOLEO_MCP_CONFIG` environment variable.

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_search_stations` | Search stations by name |
| `tool_get_station_info` | Station address, hours, facilities |
| `tool_get_departures` | Departures from a station |
| `tool_get_arrivals` | Arrivals at a station |
| `tool_get_all_trains` | All trains (dep+arr) at a station |
| `tool_search_connections` | Find connections A->B |
| `tool_get_train_route` | Train route by brand+number |
| `tool_get_train_by_id` | Train route by Koleo ID |
| `tool_get_train_calendar` | Operating dates for a train |
| `tool_get_realtime_timetable` | Live timetable (auth required) |
| `tool_get_seat_stats` | Seat occupancy on a route |
| `tool_get_seat_availability` | Raw seat map by connection ID |
| `tool_get_brands` | List all train brands |
| `tool_get_carriers` | List all carriers |
