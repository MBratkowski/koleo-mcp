import json

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
    query: str,
    type: str | None = None,
    country: str | None = None,
) -> str:
    """
    Args:
        query: Station name to search for (e.g. 'Krakow', 'Warszawa')
        type: Optional filter by type: 'rail', 'bus', 'group'
        country: Optional filter by country code: 'pl', 'de', etc.
    """
    return json.dumps(await search_stations(query, type, country), ensure_ascii=False)


@mcp.tool(description="Get detailed info about a station: address, opening hours, available facilities.")
async def tool_get_station_info(station: str) -> str:
    """
    Args:
        station: Station name (e.g. 'Krakow Glowny') or slug (e.g. 'krakow-glowny')
    """
    return json.dumps(await get_station_info(station), ensure_ascii=False)


@mcp.tool(description="Get upcoming train departures from a station.")
async def tool_get_departures(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name (e.g. 'Krakow Glowny') or slug
        date: ISO datetime (e.g. '2026-02-27T14:00'). Defaults to now.
    """
    return json.dumps(await get_departures(station, date), ensure_ascii=False)


@mcp.tool(description="Get upcoming train arrivals at a station.")
async def tool_get_arrivals(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name or slug
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_arrivals(station, date), ensure_ascii=False)


@mcp.tool(description="Get all trains (both departures and arrivals) at a station, sorted by time.")
async def tool_get_all_trains(station: str, date: str | None = None) -> str:
    """
    Args:
        station: Station name or slug
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_all_trains(station, date), ensure_ascii=False)


@mcp.tool(description="Search for train connections between two stations.")
async def tool_search_connections(
    start: str,
    end: str,
    date: str | None = None,
    brands: list[str] | None = None,
    direct: bool = False,
    include_prices: bool = False,
    length: int = 5,
) -> str:
    """
    Args:
        start: Starting station name (e.g. 'Krakow') or slug
        end: Destination station name or slug
        date: ISO datetime for departure after. Defaults to now.
        brands: Optional list of brand codes to filter (e.g. ['IC', 'REG'])
        direct: If True, only return direct trains (no changes)
        include_prices: If True, fetch prices for each connection
        length: Maximum number of connections to return (default 5)
    """
    return json.dumps(
        await search_connections(start, end, date, brands, direct, include_prices, length),
        ensure_ascii=False,
    )


@mcp.tool(description="Get the full route and stop schedule for a train by brand and number.")
async def tool_get_train_route(
    brand: str,
    train_number: str,
    date: str | None = None,
    closest: bool = False,
) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG', 'EIC', 'KM')
        train_number: Train number as string (e.g. '1106', '10417')
        date: ISO date/datetime. Defaults to today.
        closest: If True, find the closest running date if train does not run on given date.
    """
    return json.dumps(await get_train_route(brand, train_number, date, closest), ensure_ascii=False)


@mcp.tool(description="Get a train's route and stops by its internal Koleo ID.")
async def tool_get_train_by_id(train_id: int) -> str:
    """
    Args:
        train_id: Koleo internal train ID (integer)
    """
    return json.dumps(await get_train_by_id(train_id), ensure_ascii=False)


@mcp.tool(description="Get all dates when a specific train runs (operating calendar).")
async def tool_get_train_calendar(brand: str, train_number: str) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG')
        train_number: Train number as string
    """
    return json.dumps(await get_train_calendar(brand, train_number), ensure_ascii=False)


@mcp.tool(description="Check seat occupancy statistics for a train on a given route segment.")
async def tool_get_seat_stats(
    brand: str,
    train_number: str,
    stations: list[str],
    date: str | None = None,
) -> str:
    """
    Args:
        brand: Brand code (e.g. 'IC', 'REG')
        train_number: Train number as string
        stations: List of exactly 2 stations: [start_station, end_station]
        date: ISO datetime. Defaults to now.
    """
    return json.dumps(await get_seat_stats(brand, train_number, date, stations), ensure_ascii=False)


@mcp.tool(description="Get raw seat availability for a connection by connection_id, train_nr, and place_type.")
async def tool_get_seat_availability(connection_id: int, train_nr: int, place_type: int) -> str:
    """
    Args:
        connection_id: Koleo connection ID (integer)
        train_nr: Train number (integer)
        place_type: Seat/place type ID (integer, e.g. 1 for standard)
    """
    return json.dumps(await get_seat_availability(connection_id, train_nr, place_type), ensure_ascii=False)


@mcp.tool(description="List all available train brands/operators (IC, REG, EIC, KM, etc.).")
async def tool_get_brands() -> str:
    return json.dumps(await get_brands(), ensure_ascii=False)


@mcp.tool(description="List all train carriers (PKP Intercity, POLREGIO, etc.).")
async def tool_get_carriers() -> str:
    return json.dumps(await get_carriers(), ensure_ascii=False)


@mcp.tool(description="Get realtime timetable for a train, including actual vs scheduled times. Requires authentication in config.")
async def tool_get_realtime_timetable(train_id: int, operating_day: str | None = None) -> str:
    """
    Args:
        train_id: Koleo internal train ID (integer)
        operating_day: ISO date (e.g. '2026-02-27'). Defaults to today.
    """
    return json.dumps(await get_realtime_timetable(train_id, operating_day), ensure_ascii=False)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
