from datetime import datetime

from client import get_client
from config import load_config
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
            summary_lines.append(f"  {aimed} -> {actual}  station_id={s['station_id']}{delayed}")

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
