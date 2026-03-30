"""MCP server for observability tools (VictoriaLogs and VictoriaTraces)."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Settings:
    victorialogs_url: str
    victoriatraces_url: str


def resolve_settings() -> Settings:
    victorialogs_url = os.environ.get(
        "NANOBOT_VICTORIALOGS_URL", "http://victorialogs:9428"
    )
    victoriatraces_url = os.environ.get(
        "NANOBOT_VICTORIATRACES_URL", "http://victoriatraces:10428"
    )
    return Settings(victorialogs_url=victorialogs_url, victoriatraces_url=victoriatraces_url)


# Tool argument schemas
class LogsSearchArgs(BaseModel):
    query: str = Field(description="LogsQL query string (e.g., 'service.name:backend severity:ERROR')")
    limit: int = Field(default=100, ge=1, le=1000, description="Max number of log entries to return")


class LogsErrorCountArgs(BaseModel):
    minutes: int = Field(default=60, ge=1, le=1440, description="Time window in minutes")
    service: str = Field(default="", description="Optional service name filter")


class TracesListArgs(BaseModel):
    service: str = Field(description="Service name to search traces for")
    limit: int = Field(default=10, ge=1, le=100, description="Max number of traces to return")


class TracesGetArgs(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


async def logs_search(client: httpx.AsyncClient, settings: Settings, args: LogsSearchArgs) -> str:
    """Search VictoriaLogs using LogsQL query."""
    url = f"{settings.victorialogs_url}/select/logsql/query"
    params = {"query": args.query, "limit": args.limit}
    resp = await client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


async def logs_error_count(client: httpx.AsyncClient, settings: Settings, args: LogsErrorCountArgs) -> str:
    """Count errors per service over a time window."""
    time_range = f"{args.minutes}m"
    query = f"_time:{time_range} severity:ERROR"
    if args.service:
        query += f' service.name:"{args.service}"'
    
    url = f"{settings.victorialogs_url}/select/logsql/stats_query"
    params = {"query": query, "time": time_range}
    resp = await client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.text


async def traces_list(client: httpx.AsyncClient, settings: Settings, args: TracesListArgs) -> str:
    """List recent traces for a service."""
    url = f"{settings.victoriatraces_url}/select/jaeger/api/traces"
    params = {"service": args.service, "limit": args.limit}
    resp = await client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return json.dumps(data, indent=2)


async def traces_get(client: httpx.AsyncClient, settings: Settings, args: TracesGetArgs) -> str:
    """Fetch a specific trace by ID."""
    url = f"{settings.victoriatraces_url}/select/jaeger/api/traces/{args.trace_id}"
    resp = await client.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return json.dumps(data, indent=2)


def create_server(settings: Settings) -> Server:
    server = Server("mcp-obs")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="logs_search",
                description="Search VictoriaLogs using LogsQL query. Use fields like service.name, severity, event, trace_id.",
                inputSchema=LogsSearchArgs.model_json_schema(),
            ),
            Tool(
                name="logs_error_count",
                description="Count errors per service over a time window. Returns error statistics.",
                inputSchema=LogsErrorCountArgs.model_json_schema(),
            ),
            Tool(
                name="traces_list",
                description="List recent traces for a service from VictoriaTraces.",
                inputSchema=TracesListArgs.model_json_schema(),
            ),
            Tool(
                name="traces_get",
                description="Fetch a specific trace by ID from VictoriaTraces.",
                inputSchema=TracesGetArgs.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        async with httpx.AsyncClient() as client:
            try:
                if name == "logs_search":
                    args = LogsSearchArgs.model_validate(arguments or {})
                    result = await logs_search(client, settings, args)
                elif name == "logs_error_count":
                    args = LogsErrorCountArgs.model_validate(arguments or {})
                    result = await logs_error_count(client, settings, args)
                elif name == "traces_list":
                    args = TracesListArgs.model_validate(arguments or {})
                    result = await traces_list(client, settings, args)
                elif name == "traces_get":
                    args = TracesGetArgs.model_validate(arguments or {})
                    result = await traces_get(client, settings, args)
                else:
                    result = f"Unknown tool: {name}"
                return [TextContent(type="text", text=result)]
            except Exception as exc:
                return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]

    return server


async def main() -> None:
    settings = resolve_settings()
    server = create_server(settings)
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
