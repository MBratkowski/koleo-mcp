import json

from mcp.server.fastmcp import FastMCP

from tools.board import get_all_trains, get_arrivals, get_departures
from tools.connections import search_connections
from tools.stations import get_station_info, search_stations

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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
