import asyncio

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
        st, info = await asyncio.gather(
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
