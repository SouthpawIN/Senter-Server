#!/usr/bin/env python3
"""Senter-Server MCP Model Router - Routes requests to model endpoints for Hermes Agent."""

import json, os, sys, requests
from typing import Dict, List, Any, Optional

CONFIG = {
    "text_endpoint": os.environ.get("SENTER_BASE_URL", "http://127.0.0.1:8100"),
    "omni_endpoint": os.environ.get("SENTER_OMNI_URL", "http://127.0.0.1:8101"),
    "tts_endpoint": os.environ.get("SENTER_TTS_URL", "http://127.0.0.1:8102"),
    "video_endpoint": os.environ.get("SENTER_VIDEO_URL", "http://127.0.0.1:8105"),
    "music_endpoint": os.environ.get("SENTER_MUSIC_URL", "http://127.0.0.1:8106"),
    "image_gen_endpoint": os.environ.get("SENTER_IMAGE_GEN_URL", "http://127.0.0.1:8108"),
    "image_edit_endpoint": os.environ.get("SENTER_IMAGE_EDIT_URL", "http://127.0.0.1:8109"),
}

MODELS = {
    "qwen35_1m": {"name": "Qwen3.5-35B-A3B (1M)", "type": "text", "endpoint": CONFIG["text_endpoint"], 
                  "context_window": 1000000, "capabilities": ["reasoning", "long-context"]},
    "qwen35": {"name": "Qwen3.5-35B-A3B", "type": "text", "endpoint": CONFIG["text_endpoint"],
               "context_window": 262144, "capabilities": ["reasoning"]},
    "qwen27": {"name": "Qwen3.5-27B", "type": "text", "endpoint": CONFIG["text_endpoint"],
              "context_window": 262144, "capabilities": ["reasoning"]},
    "qwen_omni": {"name": "Qwen2.5-Omni-3B", "type": "vision", "endpoint": CONFIG["omni_endpoint"],
                  "context_window": 8192, "capabilities": ["vision", "audio"]},
    "soprano_tts": {"name": "Soprano 80M", "type": "tts", "endpoint": CONFIG["tts_endpoint"],
                    "capabilities": ["text-to-speech"]},
    "image_gen": {"name": "Qwen Image Gen", "type": "image_gen", "endpoint": CONFIG["image_gen_endpoint"],
                  "capabilities": ["image-generation"]},
    "ltx_video": {"name": "LTX-Video", "type": "video_gen", "endpoint": CONFIG["video_endpoint"],
                   "capabilities": ["video-generation"]},
    "acestep_music": {"name": "AceStep", "type": "music_gen", "endpoint": CONFIG["music_endpoint"],
                      "capabilities": ["music-generation"]},
}

class ModelRouter:
    def __init__(self):
        self.active_models = {name: True for name in MODELS}
        
    def list_models(self, model_type=None):
        result = []
        for name, model in MODELS.items():
            if model_type and model.get("type") != model_type:
                continue
            result.append({"name": name, **model, "is_active": self.active_models.get(name, True)})
        return result
    
    def text_inference(self, messages, model="qwen35", temperature=0.7, max_tokens=4096):
        try:
            resp = requests.post(f"{CONFIG['text_endpoint']}/v1/chat/completions",
                               json={"messages": messages, "temperature": temperature, "max_tokens": max_tokens},
                               timeout=120)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def vision_inference(self, image_url, prompt, temperature=0.7):
        messages = [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": prompt}
        ]}]
        try:
            resp = requests.post(f"{CONFIG['omni_endpoint']}/v1/chat/completions",
                               json={"messages": messages, "temperature": temperature}, timeout=120)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def tts_synthesis(self, text, voice="default"):
        try:
            resp = requests.post(f"{CONFIG['tts_endpoint']}/v1/audio/speech",
                               json={"input": text, "voice": voice}, timeout=60)
            return {"status": "success", "audio_bytes": len(resp.content), "format": "wav"}
        except Exception as e:
            return {"error": str(e)}
    
    def check_health(self, model_name):
        model = MODELS.get(model_name)
        if not model: return {"healthy": False, "error": "Model not found"}
        try:
            for path in ["/health", "/v1/models", "/"]:
                try:
                    resp = requests.get(f"{model['endpoint']}{path}", timeout=5)
                    if resp.status_code < 400:
                        return {"healthy": True, "model": model_name, "endpoint": model["endpoint"]}
                except: continue
            return {"healthy": False, "error": "No healthy endpoint"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def get_system_status(self):
        status = {}
        for name in MODELS: status[name] = self.check_health(name)
        healthy = sum(1 for m in status.values() if m.get("healthy", False))
        return {"status": "healthy" if healthy == len(status) else "degraded",
                "healthy_models": healthy, "total_models": len(status), "details": status}

router = ModelRouter()

def handle_initialize(params):
    return {"jsonrpc": "2.0", "result": {
        "protocolVersion": "2024-11-05", "capabilities": {"tools": {}, "resources": {}},
        "serverInfo": {"name": "senter-model-router", "version": "1.0.0"}}, "id": params.get("id")}

def handle_list_tools(params):
    return {"jsonrpc": "2.0", "result": {
        "tools": [{"name": "list_models", "description": "List available models",
                   "inputSchema": {"type": "object", "properties": {
                       "model_type": {"type": "string", "enum": ["text", "vision", "tts"]}}}},
                  {"name": "get_model_info", "description": "Get model details",
                   "inputSchema": {"type": "object", "properties": {"model_name": {"type": "string"}}, "required": ["model_name"]}},
                  {"name": "text_inference", "description": "Text generation",
                   "inputSchema": {"type": "object", "properties": {
                       "messages": {"type": "string"}, "model": {"type": "string", "default": "qwen35"}}, "required": ["messages"]}},
                  {"name": "vision_inference", "description": "Vision analysis",
                   "inputSchema": {"type": "object", "properties": {
                       "image_url": {"type": "string"}, "prompt": {"type": "string"}}, "required": ["image_url", "prompt"]}},
                  {"name": "tts_synthesis", "description": "Text-to-speech",
                   "inputSchema": {"type": "object", "properties": {
                       "text": {"type": "string"}, "voice": {"type": "string", "default": "default"}}, "required": ["text"]}},
                  {"name": "check_model_health", "description": "Check model health",
                   "inputSchema": {"type": "object", "properties": {"model_name": {"type": "string"}}, "required": ["model_name"]}},
                  {"name": "get_system_status", "description": "Get system status",
                   "inputSchema": {"type": "object", "properties": {}}}]}, "id": params.get("id")}

def handle_tool_call(params):
    call = params.get("params", {})
    tool_name = call.get("name", "")
    args = call.get("arguments", {})
    try:
        if tool_name == "list_models": result = router.list_models(args.get("model_type"))
        elif tool_name == "get_model_info": result = MODELS.get(args.get("model_name", ""), {"error": "Not found"})
        elif tool_name == "text_inference": result = router.text_inference(json.loads(args.get("messages", "[]")), args.get("model", "qwen35"))
        elif tool_name == "vision_inference": result = router.vision_inference(args.get("image_url", ""), args.get("prompt", ""))
        elif tool_name == "tts_synthesis": result = router.tts_synthesis(args.get("text", ""))
        elif tool_name == "check_model_health": result = router.check_health(args.get("model_name", ""))
        elif tool_name == "get_system_status": result = router.get_system_status()
        else: result = {"error": f"Unknown tool: {tool_name}"}
        return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}, "id": params.get("id")}
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": str(e)}, "id": params.get("id")}

def main():
    print("Senter-Server MCP Model Router v1.0.0", file=sys.stderr)
    for line in sys.stdin:
        if not line.strip(): continue
        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            if method == "initialize": response = handle_initialize(msg)
            elif method == "tools/list": response = handle_list_tools(msg)
            elif method == "tools/call": response = handle_tool_call(msg)
            else: response = {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Unknown method"}, "id": msg.get("id")}
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError: continue
        except Exception as e: print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}), flush=True)

if __name__ == "__main__": main()
