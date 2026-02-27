import json

from mcp.server.fastmcp import FastMCP

from tools.board import get_all_trains, get_arrivals, get_departures
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
