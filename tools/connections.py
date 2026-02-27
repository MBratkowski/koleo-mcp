from asyncio import gather
from datetime import datetime, timedelta

from koleo.utils import koleo_time_to_dt, name_to_slug

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
