# Senter Server 🎯

**Peak Performance Multimodal AI Server for Hermes Agent Ecosystem**

Senter Server is a complete turnkey solution for running a local multimodal AI server with smart model switching, hardware detection, and seamless integration with the Hermes Agent framework. Built for the Hermes Hackathon as a scalable, production-ready backend for voice-first, device-integrated AI assistance.

---

## 🚀 Features

### Complete Model Stack (9 Services)
- **Qwen3.5-35B-A3B** - Ultra-long context (1M tokens with YaRN scaling)
- **Qwen3.5-35B-A3B** - Standard mode (262K context, ~80 tokens/sec)
- **Qwen3.5-27B** - High-quality reasoning (Q6_K quantization)
- **Qwen2.5-Omni-3B** - Multimodal vision and audio understanding
- **Soprano 80M** - Fast local text-to-speech synthesis
- **Qwen Image** - Image generation server
- **Qwen Edit** - Image editing server
- **LTX-Video** - Video generation (2B parameters)
- **AceStep** - Music generation (1.5B parameters)

### Hardware Flexibility
- **PEAK Profile**: All 9 models (dual 24GB GPUs, 48GB+ VRAM)
- **HIGH Profile**: 7 models, no video (single 24GB GPU)
- **MEDIUM Profile**: 5 models, smaller LLMs (12-16GB VRAM)
- **BASIC Profile**: 3 models, minimal requirements (6-8GB VRAM)
- **CPU Profile**: 2 small models, CPU-only mode

### Smart Features
- Automatic hardware detection and profile recommendation
- Smart VRAM management with model switching
- TailScale integration for secure remote access
- One-command installation and setup
- Production-ready logging and monitoring

---

## 📋 Quick Start

### Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/SouthpawIN/Senter-Server
cd Senter-Server

# Run the automated installer
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will:
1. Detect your hardware (GPU VRAM, CPU cores)
2. Recommend an appropriate profile
3. Install TailScale for remote access
4. Build llama.cpp with optimizations
5. Set up all directories and configurations

### Download Models

```bash
# Download models for your profile
./scripts/download-models.sh peak    # All 9 models (~60GB)
./scripts/download-models.sh high    # 7 models, no video (~45GB)
./scripts/download-models.sh medium  # 5 models, smaller LLMs (~25GB)
./scripts/download-models.sh basic   # 3 models, minimal (~10GB)
./scripts/download-models.sh cpu     # 2 smallest models (~5GB)
```

### Start Services

```bash
# Start all services for your profile
senter-server start-all

# Or start specific models
senter-server start qwen35      # Main LLM (262K context)
senter-server start qwen35-1m   # 1M context mode
senter-server start qwen-omni   # Multimodal vision/audio
senter-server start soprano     # TTS service

# Check status
senter-server status

# Stop all services
senter-server stop-all
```

---

## 🏗️ Architecture

### Three-Tier Design

```
┌─────────────────────────────────────────────┐
│          Senter Server                      │
│      100.84.195.22 (TailScale)              │
│                                             │
│  LLM Port :8100/v1   (model switching)     │
│  Image    :8108/v1                         │
│  Edit     :8109/v1                         │
│  TTS      :8102/                           │
│  Music    :8106/v1                         │
│  Video    :8105/                           │
└───────────────────┬─────────────────────────┘
                    │ TailScale VPN
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌──▼──────┐ ┌─▼────────┐
│  Phone       │ │ Desktop  │ │ Web      │
│ (Termux)     │ │ Client   │ │ Browser  │
│ Hermes Agent │ │          │ │          │
└──────────────┘ └──────────┘ └──────────┘
```

### Model Switching Strategy

All LLMs share port 8100/v1 with automatic switching:
- **qwen35-1m**: Best for long documents, codebases (1M tokens)
- **qwen35**: Default mode, best speed/quality balance (~80 tok/s)
- **qwen27**: Alternative reasoning model, slightly smaller
- **qwen-omni**: Multimodal tasks with vision/audio input

---

## 📱 Hermes Agent Integration

### As a Skill

```bash
cd ~/.hermes-agent/skills
git clone https://github.com/SouthpawIN/Senter-Server senter-server
ln -s ~/Senter-Server/bin/senter-server ~/.hermes-agent/bin/
```

### Tool Calling Examples

**Speaking through phone (using Soprano TTS):**
```python
def speak_to_phone(text: str, device: str = "duo") -> str:
    """Speak text through phone using Soprano TTS"""
    # Ensure Soprano is running
    subprocess.run(["senter-server", "ensure-running", "soprano"])
    
    # Use speak.py skill to route audio
    result = subprocess.run([
        "python3", "/home/sovthpaw/Senter/skills/speak/speak.py",
        text, "--device", device, "--if-on"
    ], capture_output=True, text=True)
    
    return result.stdout
```

**Model switching for different tasks:**
```python
def select_model_for_task(task_type: str) -> str:
    """Select appropriate model based on task"""
    if task_type == "long_context":
        senter_server("start", "qwen35-1m")
        return "qwen3.5-35b-a3b-1m"
    elif task_type == "multimodal":
        senter_server("start", "qwen-omni")
        return "qwen2.5-omni-3b"
    else:
        senter_server("start", "qwen35")
        return "qwen3.5-35b-a3b"
```

---

## 🔧 Configuration

### Hardware Detection

Run `./scripts/detect-hardware.sh` to see detected hardware:
```
Detected NVIDIA GPUs:
  NVIDIA GeForce RTX 3090, 24576
  NVIDIA GeForce RTX 3090, 24576

Hardware Summary:
  GPU Count: 2
  Total VRAM: 49152MB
  CPU Cores: 16
```

### Profile Selection

Based on VRAM:
- **≥46GB**: PEAK (all models)
- **≥20GB**: HIGH (no video)
- **≥12GB**: MEDIUM (smaller LLMs)
- **≥6GB**: BASIC (minimal)
- **<6GB or CPU**: CPU mode

### Manual Configuration

Edit `~/.senter-server/config/server.conf`:
```bash
TAILSCALE_IP=100.84.195.22
MODELS_DIR=/home/user/.senter-server/models
LOG_DIR=/home/user/.senter-server/logs
PORT_LLM=8100
CONFIG_PROFILE=peak
```

---

## 🌐 TailScale Setup

### Why TailScale?
- Secure VPN for remote access to your server
- No port forwarding needed
- End-to-end encryption
- Works behind NAT/firewalls

### Quick Setup

```bash
# Install TailScale (if not done by installer)
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled

# Connect to your TailScale network
tailscale up

# Get your server's IP
tailscale ip
# Example: 100.84.195.22
```

### Access from Remote Devices

From any device on your TailScale network:
```bash
# Test LLM endpoint
curl http://100.84.195.22:8100/v1/models

# From phone (Termux)
ssh -p 8022 droid@YOUR_PHONE_IP "curl http://100.84.195.22:8100/v1/models"
```

---

## 📊 Model Specifications

### LLM Models

| Model | Size | Context | VRAM | Speed | Use Case |
|-------|------|---------|------|-------|----------|
| Qwen3.5-35B-A3B (1M) | 22GB | 1M tokens | 26GB | ~40 tok/s | Long documents, codebases |
| Qwen3.5-35B-A3B | 22GB | 262K tokens | 26GB | ~80 tok/s | General reasoning |
| Qwen3.5-27B | 17GB | 262K tokens | 20GB | ~60 tok/s | Alternative reasoning |
| Qwen2.5-Omni-3B | 4GB | 8K tokens | 6GB | ~100 tok/s | Vision/audio tasks |
| Qwen2.5-7B | 5GB | 32K tokens | 7GB | ~120 tok/s | Limited VRAM |
| Qwen2.5-3B | 2GB | 8K tokens | 4GB | ~150 tok/s | CPU/basic mode |

### Specialized Services

| Service | Port | Type | VRAM | Purpose |
|---------|------|------|------|---------|
| Soprano | 8102 | TTS | <1GB | Text-to-speech |
| Qwen Image | 8108 | Generation | 8GB+ | Image creation |
| Qwen Edit | 8109 | Editing | 8GB+ | Image modification |
| LTX-Video | 8105 | Video | 12GB+ | Video generation |
| AceStep | 8106 | Music | 6GB+ | Music generation |

---

## 🧪 Testing & API Usage

### Test LLM Endpoint

```bash
curl http://localhost:8100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5-35b-a3b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello! Explain quantum computing in simple terms."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Test TTS (Soprano)

```bash
curl -X POST http://localhost:8102/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test of the text-to-speech system.",
    "voice": "default"
  }' \
  -o output.wav

# Play the audio
ffplay output.wav
```

### Test Multimodal (Qwen-Omni)

```bash
# With image input
curl http://localhost:8100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-omni-3b",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
          {"type": "text", "text": "What do you see in this image?"}
        ]
      }
    ]
  }'
```

---

## 📈 Monitoring & Logging

### Check Service Status

```bash
senter-server status
```

Output:
```
=== Senter Server Status ===

LLM (port 8100):
  Running: qwen3.5-35b-a3b ✓

Soprano TTS (port 8102):
  Running ✓

=== VRAM Usage ===
  NVIDIA GeForce RTX 3090, 24576, 18834, 5742
  NVIDIA GeForce RTX 3090, 24576, 15804, 8772

=== Endpoints ===
  LLM:     http://100.84.195.22:8100/v1
  TTS:     http://100.84.195.22:8102/
```

### View Logs

```bash
# Real-time logs
tail -f ~/.senter-server/logs/qwen35.log
tail -f ~/.senter-server/logs/soprano.log

# Recent errors
grep -i error ~/.senter-server/logs/*.log | tail -20
```

### VRAM Monitoring

```bash
# Continuous monitoring
watch -n 1 nvidia-smi

# One-time detailed view
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu --format=csv
```

---

## 🐛 Troubleshooting

### Model Won't Start

```bash
# Check if port is in use
ss -tlnp | grep 8100

# Kill stale processes
fuser -k 8100/tcp
pkill -f llama-server

# Check logs for errors
tail -50 ~/.senter-server/logs/qwen35.log
```

### "Model not found" Error

```bash
# Download missing models
./scripts/download-models.sh peak

# Verify model files exist
ls -lh ~/.senter-server/models/Qwen3.5-35B-A3B-GGUF/
```

### Slow Performance

```bash
# Check if using GPU
nvidia-smi | grep llama-server

# If not, verify CUDA is working
export LD_LIBRARY_PATH=/home/sovthpaw/Senter-Server/bin:$LD_LIBRARY_PATH

# Restart with correct path
senter-server restart qwen35
```

### TailScale Connection Issues

```bash
# Verify TailScale is running
tailscale status

# Check server IP
tailscale ip

# Update config if IP changed
echo "TAILSCALE_IP=NEW_IP" >> ~/.senter-server/config/server.conf
```

---

## 🎯 Use Cases

### 1. Hermes Agent Backend (Primary)

Senter Server is designed as the backend for Hermes Agent with:
- Burner-phone skill integration (voice conversations)
- Multimodal processing (vision, audio, text)
- Long-context support for code analysis
- TTS for voice responses via phone

### 2. Personal AI Assistant

Run locally for privacy:
- No cloud dependencies
- Full control over data
- Voice-first interaction via phone
- Secure remote access via TailScale

### 3. Development & Testing

Perfect for AI development:
- Multiple models for A/B testing
- Fast iteration with local serving
- API-compatible with OpenAI format
- Easy model switching

---

## 🤝 Contributing to Hermes Agent

Senter Server is built as a contribution to the Hermes Agent ecosystem:

### Planned PRs to NousResearch

1. **Multimodal Server Skill** - Model management for voice assistants
2. **Phone Assistant Enhancement** - Burner-phone integration improvements
3. **Hardware Detection Pattern** - Adaptive model selection based on resources
4. **TailScale Networking** - Secure remote access patterns
5. **Peak Performance Configurations** - Optimized model settings

### Code Style

- Follow Hermes Agent conventions
- Document all tool calls
- Include error handling
- Write tests for new features

---

## 📚 Documentation

- **[MODELS.md](MODELS.md)** - Detailed model specifications and download links
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and components
- **[scripts/README.md](scripts/README.md)** - Script usage and examples
- **[HACKATHON_OVERVIEW.md](HACKATHON_OVERVIEW.md)** - Hackathon submission details

---

## 🎯 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Hardware detection and profile selection
- [x] Model manager with smart switching
- [x] Installation script with dependencies
- [x] TailScale integration
- [x] Basic documentation

### Phase 2: Hermes Integration 🚧
- [ ] Official skill PR to NousResearch
- [ ] Burner-phone voice conversation flow
- [ ] Tool calling examples and patterns
- [ ] Multi-device audio routing

### Phase 3: Advanced Features 🔜
- [ ] Web dashboard for monitoring
- [ ] Model download manager GUI
- [ ] Automatic model updates
- [ ] Multi-user profiles
- [ ] Mobile app (beyond Termux)

---

## 📄 License

MIT License - see LICENSE file for details.

Built for the **Hermes Agent Hackathon** with love ❤️

### Related Projects
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - The foundation
- [Burner Phone](https://github.com/SouthpawIN/burner-phone) - Device control framework
- [Soprano TTS](https://github.com/suno-ai/soprano) - Fast local TTS
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Efficient inference

---

## 🙏 Acknowledgments

Built by **SouthpawIN** as part of the Hermes Agent community.

This project demonstrates what's possible when combining:
- Open-source LLMs (Qwen series)
- Efficient inference (llama.cpp)
- Voice-first design (Soprano TTS)
- Secure networking (TailScale)
- Mobile integration (Termux + SSH)

---

*Made with 🎵 for the open-source AI agent revolution | Checkpoint: March 2026*