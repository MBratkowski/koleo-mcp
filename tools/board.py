from asyncio import gather
from datetime import datetime

from koleo.utils import name_to_slug

from client import get_client
from errors import handle_tool_error
from formatters.board import summarize_board


async def _resolve_station(station: str):
    client = get_client()
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
            "summary": f"{st['name']} -- all trains on {dt.strftime('%Y-%m-%d %H:%M')}:\n" + "\n".join(summary_lines),
            "koleo_url": f"https://koleo.pl/dworzec-pkp/{st['name_slug']}/odjazdy/{dt.strftime('%Y-%m-%d')}",
        }
    except Exception as e:
        return handle_tool_error(e)
