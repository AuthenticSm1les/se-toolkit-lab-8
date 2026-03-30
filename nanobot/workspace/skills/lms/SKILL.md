---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to the LMS (Learning Management System) backend through MCP tools. Use these tools to answer questions about labs, learners, scores, and system health.

## Available Tools

- **lms_health** - Check if the LMS backend is healthy and get the item count
- **lms_labs** - List all labs available in the LMS
- **lms_learners** - List all learners registered in the LMS
- **lms_pass_rates** - Get pass rates for a specific lab (requires `lab` parameter)
- **lms_timeline** - Get submission timeline for a specific lab (requires `lab` parameter)
- **lms_groups** - Get group performance for a specific lab (requires `lab` parameter)
- **lms_top_learners** - Get top learners for a specific lab (requires `lab` parameter, optional `limit`)
- **lms_completion_rate** - Get completion rate for a specific lab (requires `lab` parameter)
- **lms_sync_pipeline** - Trigger the LMS sync pipeline

## Strategy

### When the user asks about labs, scores, pass rates, completion, groups, timeline, or top learners:

1. **If a lab is specified** - call the relevant tool directly with the lab parameter

2. **If no lab is specified** - first call `lms_labs` to get available labs, then:
   - If there's only one lab, use it
   - If there are multiple labs, ask the user to choose one
   - Present lab options using clear labels (use the lab title from `lms_labs` response)

### When the user asks about system health:

- Call `lms_health` and report the result concisely
- Mention the item count if healthy

### When the user asks "what can you do?":

Explain your current capabilities:
- You can query the LMS backend for lab information, scores, pass rates, completion rates, timelines, group performance, and top learners
- You can check if the LMS backend is healthy
- You need a lab identifier for most detailed queries (pass rates, timeline, groups, top learners, completion rate)
- If the user doesn't specify a lab, you'll ask them to choose from available labs

## Response Format

- Keep responses concise and focused on the data
- Format numeric results nicely (e.g., percentages as "75%" not "0.75")
- Use tables for structured data when appropriate
- Don't dump raw JSON - summarize the findings

## Examples

**User:** "Show me the scores"
**You:** Call `lms_labs` first, then ask "Which lab would you like to see scores for? Here are the available labs: [list]"

**User:** "Is the backend healthy?"
**You:** Call `lms_health`, respond "Yes, the LMS backend is healthy with X items" or "No, the backend is not responding"

**User:** "What labs are available?"
**You:** Call `lms_labs`, list them in a clear format

**User:** "Show me pass rates for lab-01"
**You:** Call `lms_pass_rates` with lab="lab-01", summarize the results
