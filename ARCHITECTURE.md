# Senter Server - Unified AI Assistant Platform

## Overview

Senter Server is a comprehensive AI assistant platform that combines multimodal model serving, intelligent agent orchestration, and mobile device integration into one cohesive system. All processing happens on a central Linux server accessible via TailScale, with thin clients (phones, computers) providing interface and control.

---

## Architecture Layers

### 1. Server Layer (The Brain)
**Location:** Central Linux machine (dual RTX 3090, 48GB VRAM total)
**Access:** TailScale IP `100.84.195.22`

#### Model Stack
- **Central Reasoning Model:** Qwen3.5-27B (or Claude-distilled variant) - text + vision
- **Omni Modal Adapter:** Qwen2.5-Omni-3B - audio understanding, speech-to-text
- **TTS Engine:** Soprano 80M - text-to-speech synthesis  
- **Generation Models** (swappable based on VRAM):
  - Image generation (Stable Diffusion, Flux, etc.)
  - Video generation
  - Music/audio generation

#### Smart VRAM Management
- Models dynamically loaded/unloaded based on active tasks
- Central reasoning model stays resident when possible
- Generation models swap in/out as needed
- Tensor splitting across dual GPUs for large models

---

### 2. Three-Agent System (The Intelligence)

All agents run on the server, accessible via API:

#### Chat Agent (Uninterrupted Conversation)
- **Purpose:** Immediate user interaction, quick tasks, home automation
- **Characteristics:** Fast response, conversational, never interrupted
- **Handles:**
  - Quick web research requests
  - Home automation commands ("turn lights red")
  - One-shot questions and tasks
  - Device control via Phone Agent
- **Interface:** Voice (phone double-tap), text (web/CLI)

#### Planning Agent (Silent Observer)
- **Purpose:** Extract goals, projects, and long-term plans from conversations
- **Characteristics:** Runs silently in background, analyzes chat history
- **Processes:**
  - Monitors all chat interactions
  - Identifies user goals ("increase happiness", "improve finances")
  - Creates structured project proposals
  - Suggests plans back to Chat Agent for user confirmation
- **Output:** Confirmed projects → Worker Agent queue

#### Worker Agent (Hermes Integration)
- **Purpose:** Execute long-term tasks and projects
- **Characteristics:** Continuous background operation, multi-step workflows
- **Capabilities:**
  - File system operations
  - Code generation and execution
  - Web automation
  - Scheduled jobs via cron
  - Multi-session task persistence
- **Integration:** Hermes Agent framework with full tool access

---

### 3. Phone Agent Layer (The Embodiment)

**Location:** Android devices (Surface Duo, Samsung S10, etc.)
**Connection:** TailScale SSH + minimal Termux installation

#### Core Capabilities
- **Activation:** Double-tap side button → instant voice conversation
- **Audio Capture:** High-quality microphone input to Omni model
- **Audio Playback:** Receive TTS output from Soprano
- **Device Control:** Camera, sensors, notifications
- **Home Automation:** Local network device control

#### Minimal Phone Requirements
```bash
# Required Termux packages
pkg install python git wget curl ffmpeg tailscale

# No large models installed on phone!
# All processing happens on server via TailScale
```

---

## Data Flow

### Voice Interaction Example
```
User double-taps side button
    ↓
Phone captures audio
    ↓
Audio sent to Server (TailScale)
    ↓
Omni model: Speech-to-Text + intent understanding
    ↓
Chat Agent processes request
    ↓
Response text generated
    ↓
Soprano: Text-to-Speech
    ↓
Audio streamed back to phone
    ↓
Phone plays audio through speaker
```

### Planning Flow Example
```
User says: "I've been thinking I should get my finances in order"
    ↓
Chat Agent responds conversationally
    ↓
Planning Agent (silent) extracts goal: "Improve financial management"
    ↓
Creates project proposal with steps
    ↓
Chat Agent asks user: "Would you like me to help set up a finance tracking system?"
    ↓
User confirms
    ↓
Worker Agent (Hermes) receives job, executes in background
    ↓
Progress updates flow back through Chat Agent
```

---

## Server Components

### Model Manager (`bin/senter-server`)
```bash
# Start all core services
senter-server start-all

# Individual model control
senter-server start qwen-27b      # Central reasoning
senter-server start omni          # Audio/S2T
senter-server start soprano       # TTS
senter-server start image-gen     # Image generation (swappable)

# Status and monitoring
senter-server status
senter-server vram-usage
```

### Agent Orchestrator (`bin/agent-manager`)
```bash
# Start three-agent system
agent-manager start

# Individual agents
agent-manager start chat          # Chat agent
agent-manager start planner       # Planning agent  
agent-manager start worker        # Hermes integration

# Configuration
agent-manager config              # Set model endpoints, thresholds
```

### Phone Client (`burner-phone/`)
```bash
# Setup (run once on phone Termux)
./scripts/setup.sh

# Start voice assistant service
phone-assistant start

# Manual activation test
phone-assistant test-activation
```

---

## Network Architecture

```
                    ┌─────────────────────────────────┐
                    │      SENTER SERVER              │
                    │   100.84.195.22 (TailScale)     │
                    │                                 │
                    │  ┌──────────────────────────┐  │
                    │  │   Model Layer            │  │
                    │  │  • Qwen3.5-27B :8100    │  │
                    │  │  • Qwen-Omni   :8101    │  │
                    │  │  • Soprano     :8102    │  │
                    │  │  • Image-Gen   :8103    │  │
                    │  └──────────────────────────┘  │
                    │                                 │
                    │  ┌──────────────────────────┐  │
                    │  │   Agent Layer            │  │
                    │  │  • Chat Agent   :9000    │  │
                    │  │  • Planner      :9001    │  │
                    │  │  • Worker API   :9002    │  │
                    │  └──────────────────────────┘  │
                    └─────────────────────────────────┘
                              ↕ TailScale VPN
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌──────────────┐    ┌────────────────┐    ┌────────────────┐
│  Surface Duo │    │   Desktop PC   │    │   Laptop/Other │
│ 100.79.15.54│    │  Localhost     │    │  Remote Access │
│ Port: 8022  │    │  Web Interface │    │  Via TailScale │
└──────────────┘    └────────────────┘    └────────────────┘
```

---

## Security & Privacy

- **All data stays on user's server** - no cloud APIs
- **TailScale encryption** for all network traffic
- **SSH key authentication** for phone devices
- **Local-first design** - works completely offline within network
- **User owns all models** - GGUF files stored locally

---

## Future Extensions

### Planned Features
- [ ] Multiple user profiles with personalized models
- [ ] Plugin system for custom agent tools
- [ ] Web dashboard for monitoring and control
- [ ] Mobile app (native Android) beyond Termux
- [ ] Voice cloning for personalized TTS
- [ ] Multi-language support expansion

### Model Upgrades
- [ ] Qwen3.5-27B-Claude-4.6-Opus distillation (better reasoning)
- [ ] Larger context window models (1M+ tokens)
- [ ] Specialized domain models (medical, legal, coding)
- [ ] Real-time video understanding

---

## Quick Start

### Server Setup
```bash
# Clone and install
git clone https://github.com/SouthpawIN/Senter-Server
cd Senter-Server
./install.sh

# Configure TailScale IP
echo "TAILSCALE_IP=100.84.195.22" >> ~/.senter-config

# Start all services
senter-server start-all
```

### Phone Setup (Termux)
```bash
# Install prerequisites
pkg install -y python git curl tailscale ffmpeg

# Clone phone agent
git clone https://github.com/SouthpawIN/burner-phone
cd burner-phone
./scripts/setup.sh

# Configure server connection
echo "SERVER_IP=100.84.195.22" >> ~/.phone-agent-config

# Start service
phone-assistant start
```

### First Interaction
1. Double-tap side button on phone
2. Say: "Hey Senter, what can you do?"
3. Chat Agent responds with capabilities
4. Try: "Turn my living room lights blue" (if integrated)
5. Or: "Research the best way to learn Spanish"

---

## Monitoring & Debugging

```bash
# Server health
senter-server status
agent-manager status

# VRAM usage
nvidia-smi

# Agent logs
tail -f /var/log/senter/chat-agent.log
tail -f /var/log/senter/planner.log
tail -f /var/log/senter/worker.log

# Phone connection test
ssh -p 8022 droid@100.79.15.54 "echo ok"
```

---

## Philosophy

**Senter Server** embodies these principles:

1. **User Sovereignty:** You own your AI, your data, your models
2. **Continuous Availability:** Chat never interrupted, workers always helping
3. **Proactive Intelligence:** System learns your goals and suggests improvements
4. **Unified Experience:** One system for conversation, automation, and creation
5. **Privacy First:** Everything local, encrypted, under your control

---

*Built for the Hermes Hackathon | Open Source MIT License*