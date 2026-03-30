# MCP Observability Server

MCP server providing tools for querying VictoriaLogs and VictoriaTraces.

## Tools

- `logs_search` - Search logs using LogsQL
- `logs_error_count` - Count errors per service
- `traces_list` - List traces for a service
- `traces_get` - Get a specific trace by ID

## Usage

```bash
python -m mcp_obs
```

## Environment Variables

- `NANOBOT_VICTORIALOGS_URL` - VictoriaLogs URL (default: http://victorialogs:9428)
- `NANOBOT_VICTORIATRACES_URL` - VictoriaTraces URL (default: http://victoriatraces:10428)
