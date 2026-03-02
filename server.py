import json
import os
from pydantic import Field
from typing import Annotated

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from mcp.server.fastmcp import FastMCP

from tools.board import get_all_trains, get_arrivals, get_departures
from tools.connections import search_connections
from tools.realtime import get_realtime_timetable
from tools.seats import get_brands, get_carriers, get_seat_availability, get_seat_stats
from tools.stations import get_station_info, search_stations
from tools.trains import get_train_by_id, get_train_calendar, get_train_route

mcp = FastMCP("koleo")


@mcp.tool(description="Search for train stations by name. Returns station IDs, slugs, and types.")
async def tool_search_stations(
    query: Annotated[str, Field(description="Station name to search for (e.g. 'Krakow', 'Warszawa')")],
    type: Annotated[str | None, Field(description="Optional filter by type: 'rail', 'bus', 'group'")] = None,
    country: Annotated[str | None, Field(description="Optional filter by country code: 'pl', 'de', etc.")] = None,
) -> str:
    return json.dumps(await search_stations(query, type, country), ensure_ascii=False)


@mcp.tool(description="Get detailed info about a station: address, opening hours, available facilities.")
async def tool_get_station_info(
    station: Annotated[str, Field(description="Station name (e.g. 'Krakow Glowny') or slug (e.g. 'krakow-glowny')")]
) -> str:
    return json.dumps(await get_station_info(station), ensure_ascii=False)


@mcp.tool(description="Get upcoming train departures from a station.")
async def tool_get_departures(
    station: Annotated[str, Field(description="Station name (e.g. 'Krakow Glowny') or slug (e.g. 'krakow-glowny')")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-02-27T14:00'). Defaults to now.")] = None
) -> str:
    return json.dumps(await get_departures(station, date), ensure_ascii=False)


@mcp.tool(description="Get upcoming train arrivals at a station.")
async def tool_get_arrivals(
    station: Annotated[str, Field(description="Station name (e.g. 'Krakow Glowny') or slug (e.g. 'krakow-glowny')")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-03-02' or 2026-02-27T14:00'). Defaults to now.")] = None
) -> str:
    return json.dumps(await get_arrivals(station, date), ensure_ascii=False)


@mcp.tool(description="Get all trains (both departures and arrivals) at a station, sorted by time.")
async def tool_get_all_trains(
    station: Annotated[str, Field(description="Station name (e.g. 'Krakow Glowny') or slug (e.g. 'krakow-glowny')")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-03-02' or 2026-02-27T14:00'). Defaults to now.")] = None
) -> str:
    return json.dumps(await get_all_trains(station, date), ensure_ascii=False)


@mcp.tool(description="Search for train connections between two stations.")
async def tool_search_connections(
    start: Annotated[str, Field(description="Starting station name (e.g. 'Krakow') or slug (e.g. 'krakow')")],
    end: Annotated[str, Field(description="Destination station name (e.g. 'Warszawa') or slug (e.g. 'warszawa')")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-03-02' or 2026-02-27T14:00'). Defaults to now.")] = None,
    brands: Annotated[list[str] | None, Field(description="Optional list of brand codes to filter (e.g. ['IC', 'REG', 'EIC', 'KM'])")] = None,
    direct: Annotated[bool, Field(description="If True, only return direct trains (no changes)")] = False,
    include_prices: Annotated[bool, Field(description="If True, fetch prices for each connection")] = False,
    length: Annotated[int, Field(description="Maximum number of connections to return (default 5)")] = 5,
) -> str:
    return json.dumps(
        await search_connections(start, end, date, brands, direct, include_prices, length),
        ensure_ascii=False,
    )


@mcp.tool(description="Get the full route and stop schedule for a train by brand and number.")
async def tool_get_train_route(
    brand: Annotated[str, Field(description="Brand code (e.g. 'IC', 'REG', 'EIC', 'KM')")],
    train_number: Annotated[str, Field(description="Train number as string (e.g. '1106', '10417')")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-03-02' or 2026-02-27T14:00'). Defaults to now.")] = None,
    closest: Annotated[bool, Field(description="If True, find the closest running date if train does not run on given date.")] = False,
) -> str:
    return json.dumps(await get_train_route(brand, train_number, date, closest), ensure_ascii=False)


@mcp.tool(description="Get a train's route and stops by its internal Koleo ID.")
async def tool_get_train_by_id(train_id: Annotated[int, Field(description="Koleo internal train ID (integer)")]) -> str:
    return json.dumps(await get_train_by_id(train_id), ensure_ascii=False)


@mcp.tool(description="Get all dates when a specific train runs (operating calendar).")
async def tool_get_train_calendar(
    brand: Annotated[str, Field(description="Brand code (e.g. 'IC', 'REG', 'EIC', 'KM')")],
    train_number: Annotated[str, Field(description="Train number as string (e.g. '1106', '10417')")],
) -> str:
    return json.dumps(await get_train_calendar(brand, train_number), ensure_ascii=False)


@mcp.tool(description="Check seat occupancy statistics for a train on a given route segment.")
async def tool_get_seat_stats(
    brand: Annotated[str, Field(description="Brand code (e.g. 'IC', 'REG', 'EIC', 'KM')")],
    train_number: Annotated[str, Field(description="Train number as string (e.g. '1106', '10417')")],
    stations: Annotated[list[str], Field(description="List of exactly 2 stations: [start_station, end_station]")],
    date: Annotated[str | None, Field(description="ISO datetime (e.g. '2026-03-02' or 2026-02-27T14:00'). Defaults to now.")] = None,
) -> str:
    return json.dumps(await get_seat_stats(brand, train_number, date, stations), ensure_ascii=False)


@mcp.tool(description="Get raw seat availability for a connection by connection_id, train_nr, and place_type.")
async def tool_get_seat_availability(
    connection_id: Annotated[int, Field(description="Koleo connection ID (integer)")],
    train_number: Annotated[int, Field(description="Train number as string (e.g. '1106', '10417')")],
    place_type: Annotated[int, Field(description="Seat/place type ID (integer, e.g. 1 for standard)")],
) -> str:
    return json.dumps(await get_seat_availability(connection_id, train_number, place_type), ensure_ascii=False)


@mcp.tool(description="List all available train brands/operators (IC, REG, EIC, KM, etc.).")
async def tool_get_brands() -> str:
    return json.dumps(await get_brands(), ensure_ascii=False)


@mcp.tool(description="List all train carriers (PKP Intercity, POLREGIO, etc.).")
async def tool_get_carriers() -> str:
    return json.dumps(await get_carriers(), ensure_ascii=False)


@mcp.tool(description="Get realtime timetable for a train, including actual vs scheduled times. Requires authentication in config.")
async def tool_get_realtime_timetable(
    train_id: Annotated[int, Field(description="Koleo internal train ID (integer)")],
    operating_day: Annotated[str | None, Field(description="ISO date (e.g. '2026-02-27'). Defaults to today.")] = None,
) -> str:
    return json.dumps(await get_realtime_timetable(train_id, operating_day), ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
