# Senter-Server MCP Integration

Model Context Protocol (MCP) for Hermes Agent integration.

## Quick Start

```bash
# Start MCP server
python3 mcp/model_router.py

# Check system status
./scripts/status-monitor.sh status

# Continuous monitoring
./scripts/status-monitor.sh monitor 30
```

## Architecture

```
Hermes Agent (MCP) -> model_router.py -> Model Endpoints
                              |
                          model_manager.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_models` | List models by type (text/vision/tts) |
| `get_model_info` | Get model details |
| `text_inference` | Text generation |
| `vision_inference` | Image analysis |
| `tts_synthesis` | Speech synthesis |
| `check_model_health` | Single model health |
| `get_system_status` | Full system status |

## Model Routing

- **Text**: qwen35_1m, qwen35, qwen27 (port 8100)
- **Vision/Audio**: qwen_omni (port 8101)  
- **TTS**: soprano_tts (port 8102)
- **Image Gen**: image_gen (port 8108)
- **Video**: ltx_video (port 8105)
- **Music**: acestep_music (port 8106)

## MCP Config

Add to Hermes config:
```json
{
  "mcp": {
    "servers": {
      "senter": {
        "command": "python3",
        "args": ["~/Documents/ObsidianVault/Senter-Server/Source/mcp/model_router.py"]
      }
    }
  }
}
```

## Model Manager CLI

```bash
python3 mcp/model_manager.py start qwen35
python3 mcp/model_manager.py stop qwen35
python3 mcp/model_manager.py status
```

## Status Monitor Modes

```bash
./scripts/status-monitor.sh status   # One-shot check
./scripts/status-monitor.sh monitor 60  # Every 60s
./scripts/status-monitor.sh alert    # Notify on changes
./scripts/status-monitor.sh json     # JSON output
```
