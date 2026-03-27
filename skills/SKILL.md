---
name: senter-mcp-integration
description: "MCP server for Senter multimodal AI backend - exposes vision, audio, text models"
trigger_conditions:
  - "Setting up Senter MCP server"
  - "Exposing AI models via MCP protocol"
tools_required:
  - "terminal"
  - "read_file"
  - "write_file"
---

# Senter MCP Integration Skill

## Overview

MCP (Model Context Protocol) server that exposes Senter's multimodal AI capabilities:
- Qwen Omni 3.5B - Multimodal understanding (video + audio)
- Qwen Vision 3B - Image/screen analysis
- Various text models - Reasoning and generation
- Soprano 80M - Text-to-speech

## MCP Server Architecture

```python
from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("Senter Multimodal AI")

@mcp.tool()
def qwen_omni_analyze(video_path: str, audio_path: str, question: str) -> str:
    """Analyze video + audio with Qwen Omni 3.5B."""
    # Upload video
    with open(video_path, 'rb') as f:
        video_files = {'file': ('video.mp4', f, 'video/mp4')}
        resp = requests.post('http://localhost:8100/upload/video', files=video_files)
    
    # Upload audio  
    with open(audio_path, 'rb') as f:
        audio_files = {'file': ('audio.wav', f, 'audio/wav')}
        resp = requests.post('http://localhost:8100/upload/audio', files=audio_files)
    
    # Send for analysis
    response = requests.post('http://localhost:8100/chat/completions', json={
        "model": "qwen-omni-3.5b",
        "messages": [{"role": "user", "content": question}],
        "media": {"video": True, "audio": True}
    })
    
    return response.json()["choices"][0]["message"]["content"]

@mcp.tool()
def qwen_vision_analyze(image_path: str, question: str) -> str:
    """Analyze image with Qwen Vision 3B."""
    with open(image_path, 'rb') as f:
        files = {'image': ('image.jpg', f, 'image/jpeg')}
        resp = requests.post('http://localhost:8081/vision', 
                           files=files, 
                           json={"question": question})
    return resp.json()["answer"]

@mcp.tool()
def soprano_tts(text: str, output_path: str = None) -> str:
    """Convert text to speech with Soprano 80M."""
    response = requests.post('http://localhost:8102/tts', json={
        "text": text,
        "output": output_path or "/tmp/soprano_output.mp3"
    })
    return response.json()["output_path"]
```

## Hermes Configuration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  senter:
    command: "python3"
    args:
      - "/home/sovthpaw/Senter/skills/senter-mcp-integration/mcp_server.py"
    timeout: 300
```

## Available Tools via MCP

| Tool | Endpoint | Description |
|------|----------|-------------|
| `qwen_omni_analyze` | :8100 | Video + Audio understanding |
| `qwen_vision_analyze` | :8081 | Image/screen analysis |
| `soprano_tts` | :8102 | Text-to-speech generation |
| `model_inference` | :8080-8090 | Various text models |

## Usage Example

```python
# In Hermes conversation:
from hermes_tools import execute_code

result = execute_code('''
from mcp_client import MCPClient

client = MCPClient("senter")

# Analyze a video clip with audio
analysis = client.call_tool(
    "qwen_omni_analyze",
    {
        "video_path": "/tmp/recording.mp4",
        "audio_path": "/tmp/audio.wav", 
        "question": "Is the person looking at the camera and speaking?"
    }
)
print(analysis)
''')
```

## Model Endpoints Reference

```python
MODEL_ENDPOINTS = {
    "qwen_omni_3.5b": {
        "url": "http://localhost:8100",
        "type": "multimodal",
        "capabilities": ["video", "audio", "text"]
    },
    "qwen_vision_3b": {
        "url": "http://localhost:8081", 
        "type": "vision",
        "capabilities": ["image", "text"]
    },
    "soprano_80m": {
        "url": "http://localhost:8102",
        "type": "tts",
        "capabilities": ["audio_generation"]
    },
    "hermes_pro_405b": {
        "url": "http://localhost:8080",
        "type": "text",
        "capabilities": ["reasoning", "generation"]
    }
}
```

## Verification

```bash
# Start MCP server
python3 /home/sovthpaw/Senter/skills/senter-mcp-integration/mcp_server.py

# Test connection
 curl http://localhost:8100/health

# List available tools
mcp list-tools senter
```

## Integration with Other Skills

- **senter-attention** - Uses qwen_omni_analyze for gaze detection
- **card-scanner-vision** - Uses qwen_vision_analyze for card ID
- **speak** - Uses soprano_tts for audio generation