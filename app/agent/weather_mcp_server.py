"""Lab 1: a local MCP server. Keep stdout reserved for MCP protocol messages."""
from typing import Literal
from mcp.server.fastmcp import FastMCP
from weather_service import get_weather_forecast_data

mcp = FastMCP("Weather Forecast MCP Server")


@mcp.tool()
def get_weather_forecast(
    city: str = "Fullerton, CA", #default value = Fullerton. 
    day: Literal["today", "tomorrow", "day_after_tomorrow"] = "today",
) -> dict:
    """
    Retrieve current, daily, and hourly weather forecasts
    for any supported city in the United States.

    Parameters:
        city: User-requested city, preferably including state.
              Examples:
              'Los Angeles, CA'
              'Seattle, WA'
              'New York, NY'
              'Chicago, IL'

        day: Forecast day; today, tomorrow, or
             day_after_tomorrow.

    Returns:
        Weather forecasts including temperature,
        precipitation probability, hourly conditions,
        and likely sunny hours.

    Always use the city requested by the user.
    Never substitute Fullerton when another city
    is explicitly provided.
    """
    return get_weather_forecast_data(city, day)


if __name__ == "__main__":
    mcp.run(transport="stdio")
