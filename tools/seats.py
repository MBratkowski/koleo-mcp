from asyncio import gather
from datetime import datetime

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
                f"{brand} {train_number} on {start_st['name']} -> {end_st['name']}:\n"
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
        lines = [f"  {c['short_name']:6} -- {c['name']}" for c in carriers]
        return {
            "data": carriers,
            "summary": "Train carriers:\n" + "\n".join(lines),
            "koleo_url": "",
        }
    except Exception as e:
        return handle_tool_error(e)
