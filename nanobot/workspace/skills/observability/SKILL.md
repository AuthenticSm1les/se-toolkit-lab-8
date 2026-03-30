---
name: observability
description: Use observability MCP tools to investigate system health and errors
always: true
---

# Observability Skill

You have access to VictoriaLogs and VictoriaTraces through MCP tools. Use these tools to investigate system health, find errors, and trace failures.

## Available Tools

- **logs_search** - Search VictoriaLogs using LogsQL query
- **logs_error_count** - Count errors per service over a time window
- **traces_list** - List recent traces for a service
- **traces_get** - Fetch a specific trace by ID

## Strategy

### When the user asks about errors or system health:

1. **Start with error count** - Call `logs_error_count` with a recent time window (e.g., 10-60 minutes) to see if there are errors

2. **Search for details** - If errors exist, call `logs_search` with a query like:
   - `_time:10m severity:ERROR service.name:"Learning Management Service"`
   - Include the specific service name if the user mentioned one

3. **Extract trace ID** - From the log results, look for a `trace_id` field

4. **Fetch the trace** - Call `traces_get` with the trace ID to see the full request flow

5. **Summarize findings** - Explain:
   - What service is failing
   - What error occurred
   - Which operation/span failed
   - Any relevant context from the trace

### LogsQL Query Tips

Common fields to filter by:
- `service.name:"Learning Management Service"` - LMS backend
- `severity:ERROR` - Error-level logs only
- `event:request_completed` - Request completion events
- `trace_id:xxx` - Specific trace
- `_time:10m` - Last 10 minutes

Example queries:
- `_time:10m service.name:"Learning Management Service" severity:ERROR`
- `_time:1h severity:ERROR | stats by(service.name)`

### When the user asks "What went wrong?" or "Check system health":

1. Call `logs_error_count` with `minutes=10` for recent errors
2. If errors exist, call `logs_search` to get details
3. If a trace_id is found, call `traces_get` to see the full trace
4. Provide a concise summary mentioning both log and trace evidence

## Response Format

- Keep responses concise
- Don't dump raw JSON - summarize the key findings
- Mention specific error messages and failing operations
- When citing trace evidence, mention which span failed and why

## Examples

**User:** "Any errors in the last hour?"
**You:** Call `logs_error_count(minutes=60)`, summarize results

**User:** "What went wrong?"
**You:** 
1. Call `logs_error_count(minutes=10)`
2. If errors, call `logs_search(query="_time:10m severity:ERROR")`
3. Extract trace_id, call `traces_get(trace_id=...)`
4. Summarize: "The LMS backend failed when querying PostgreSQL. The trace shows the db_query span failed with 'connection refused'..."

**User:** "Show me the trace for request abc123"
**You:** Call `traces_get(trace_id="abc123")`, summarize the span hierarchy and timing
