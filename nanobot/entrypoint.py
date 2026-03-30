#!/usr/bin/env python3
"""Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config at runtime, then launches nanobot gateway.
"""

import json
import os
import sys
import tempfile
from pathlib import Path


def main():
    # Add workspace package source directories to Python path
    sys.path.insert(0, "/app/mcp/mcp-lms/src")
    sys.path.insert(0, "/app/nanobot-websocket-channel/mcp-webchat/src")
    sys.path.insert(0, "/app/nanobot-websocket-channel/nanobot-webchat/src")
    
    config_path = Path("/app/nanobot/config.json")
    workspace_path = Path("/app/nanobot/workspace")
    
    # Write resolved config to temp directory (writable by any user)
    resolved_path = Path(tempfile.mktemp(suffix=".json", prefix="nanobot_config_"))

    # Read the base config
    with open(config_path) as f:
        config = json.load(f)

    # Override provider API key and base URL from env vars
    if api_key := os.environ.get("LLM_API_KEY"):
        config["providers"]["custom"]["apiKey"] = api_key

    if api_base := os.environ.get("LLM_API_BASE_URL"):
        config["providers"]["custom"]["apiBase"] = api_base

    if api_model := os.environ.get("LLM_API_MODEL"):
        config["agents"]["defaults"]["model"] = api_model

    # Override gateway host/port from env vars
    if gateway_host := os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS"):
        config["gateway"]["host"] = gateway_host

    if gateway_port := os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT"):
        config["gateway"]["port"] = int(gateway_port)

    # Override MCP server environment variables
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY", "")
    
    if lms_backend_url:
        config["tools"]["mcpServers"]["lms"]["env"] = {
            "PYTHONPATH": "/app/mcp/mcp-lms/src:/app/mcp/mcp-obs/src:/app/nanobot-websocket-channel/mcp-webchat/src:/app/nanobot-websocket-channel/nanobot-webchat/src",
            "NANOBOT_LMS_BACKEND_URL": lms_backend_url,
            "NANOBOT_LMS_API_KEY": lms_api_key,
        }
    
    # Add mcp-obs server for observability tools
    config["tools"]["mcpServers"]["obs"] = {
        "command": "python",
        "args": ["-m", "mcp_obs"],
        "env": {
            "PYTHONPATH": "/app/mcp/mcp-lms/src:/app/mcp/mcp-obs/src:/app/nanobot-websocket-channel/mcp-webchat/src:/app/nanobot-websocket-channel/nanobot-webchat/src",
            "NANOBOT_VICTORIALOGS_URL": os.environ.get("NANOBOT_VICTORIALOGS_URL", "http://victorialogs:9428"),
            "NANOBOT_VICTORIATRACES_URL": os.environ.get("NANOBOT_VICTORIATRACES_URL", "http://victoriatraces:10428"),
        },
    }

    # Configure webchat channel if enabled
    if webchat_port := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT"):
        config["channels"]["webchat"] = {
            "enabled": True,
            "host": os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS", "0.0.0.0"),
            "port": int(webchat_port),
            "allowFrom": ["*"],
        }
        # Add mcp-webchat server for UI message delivery
        if access_key := os.environ.get("NANOBOT_ACCESS_KEY"):
            config["tools"]["mcpServers"]["webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"],
                "env": {
                    "PYTHONPATH": "/app/mcp/mcp-lms/src:/app/nanobot-websocket-channel/mcp-webchat/src:/app/nanobot-websocket-channel/nanobot-webchat/src",
                    "NANOBOT_UI_RELAY_URL": f"ws://localhost:{webchat_port}",
                    "NANOBOT_ACCESS_KEY": access_key,
                },
            }

    # Write the resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}")
    print(f"Webchat channel enabled: {config.get('channels', {}).get('webchat', {}).get('enabled', False)}")

    # Launch nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            str(resolved_path),
            "--workspace",
            str(workspace_path),
        ],
    )


if __name__ == "__main__":
    main()
