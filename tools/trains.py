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
