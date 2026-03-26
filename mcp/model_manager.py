#!/usr/bin/env python3
"""Senter-Server Model Manager - Start/stop models and manage lifecycle."""

import os, sys, json, time, subprocess
from typing import Dict, Any

class ModelManager:
    MODELS = {
        "qwen35_1m": {"name": "Qwen3.5-35B-A3B (1M)", "port": 8100,
                      "model": "~/.senter-server/models/Qwen3.5-35B-A3B-GGUF/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf",
                      "ctx": 1010000, "args": ["--rope-scaling", "yarn", "--rope-scale", "4.0"]},
        "qwen35": {"name": "Qwen3.5-35B-A3B", "port": 8100,
                   "model": "~/.senter-server/models/Qwen3.5-35B-GGUF/qwen3.5-35b-a3b-q4_k_m.gguf", "ctx": 262144},
        "qwen27": {"name": "Qwen3.5-27B", "port": 8100,
                   "model": "~/.senter-server/models/Qwen3.5-27B-GGUF/qwen3.5-27b-q6_k.gguf", "ctx": 262144},
        "qwen_omni": {"name": "Qwen2.5-Omni-3B", "port": 8101,
                      "model": "~/.senter-server/models/Qwen2.5-Omni-3B-GGUF/Qwen2.5-Omni-3B-Q4_K_M.gguf",
                      "mmproj": "~/.senter-server/models/Qwen2.5-Omni-3B-GGUF/mmproj-Qwen2.5-Omni-3B-Q8_0.gguf", "ctx": 8192},
    }
    processes: Dict[str, subprocess.Popen] = {}
    
    def start(self, model_name: str) -> Dict:
        if model_name not in self.MODELS:
            return {"success": False, "error": f"Unknown model: {model_name}"}
        cfg = self.MODELS[model_name]
        # Stop conflicting models
        for n, c in self.MODELS.items():
            if n != model_name and c["port"] == cfg["port"] and n in self.processes:
                self.stop(n)
        try:
            cmd = ["llama-server", "-m", os.path.expanduser(cfg["model"]), "-p", str(cfg["port"]),
                   "-c", str(cfg.get("ctx", 4096)), "-t", "8", "-ngl", "-1"]
            if cfg.get("mmproj"): cmd.extend(["--mmproj", os.path.expanduser(cfg["mmproj"])])
            if cfg.get("args"): cmd.extend(cfg["args"])
            self.processes[model_name] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            return {"success": self._check_port(cfg["port"]), "model": model_name, "port": cfg["port"]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self, model_name: str) -> Dict:
        if model_name not in self.processes:
            return {"success": False, "error": "Not running"}
        try:
            self.processes.pop(model_name).terminate()
            return {"success": True, "message": f"Stopped {model_name}"}
        except: return {"success": False, "error": "Failed to stop"}
    
    def stop_all(self) -> Dict:
        results = []
        for name in list(self.processes.keys()): results.append(self.stop(name))
        return {"results": results}
    
    def _check_port(self, port: int) -> bool:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    
    def status(self) -> Dict:
        return {"models": {name: {"running": name in self.processes, **cfg} for name, cfg in self.MODELS.items()}}

if __name__ == "__main__":
    import argparse
    mgr = ModelManager()
    p = argparse.ArgumentParser(description="Model Manager")
    sp = p.add_subparsers(dest="cmd")
    sp.add_parser("start").add_argument("model", choices=list(ModelManager.MODELS.keys()))
    sp.add_parser("stop").add_argument("model", nargs="?", default="all")
    sp.add_parser("status")
    sp.add_parser("list")
    a = p.parse_args()
    if a.cmd == "start": print(json.dumps(mgr.start(a.model), indent=2))
    elif a.cmd == "stop": print(json.dumps(mgr.stop_all() if a.model == "all" else mgr.stop(a.model), indent=2))
    elif a.cmd == "status": print(json.dumps(mgr.status(), indent=2))
    elif a.cmd == "list": 
        for n, c in ModelManager.MODELS.items(): print(f"{n}: {c['name']} (:{c['port']})")
    else: p.print_help()
