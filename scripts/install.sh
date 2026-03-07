#!/bin/bash
# Senter Server - Complete Installation Script
# Automatically detects hardware and configures optimal setup
# Works for: Dual GPU, Single GPU, CPU-only, or mixed configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOME_DIR="${HOME}/.senter-server"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[Senter-Install]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
info() { echo -e "${CYAN}ℹ${NC} $1"; }

echo "========================================"
echo "  Senter Server Installation"
echo "  Peak Performance Model Server"
echo "========================================"
echo ""

# Step 1: Detect Hardware
log "Detecting hardware configuration..."

DETECT_SCRIPT="$ROOT_DIR/scripts/detect-hardware.sh"
if [ -f "$DETECT_SCRIPT" ]; then
    source "$DETECT_SCRIPT"
else
    echo "Hardware detection script not found, using defaults"
    GPU_COUNT=0
    TOTAL_VRAM=0
    CPU_CORES=$(nproc 2>/dev/null || echo 4)
fi

echo ""
info "Hardware detected:"
echo "  GPU Count: $GPU_COUNT"
echo "  Total VRAM: ${TOTAL_VRAM}MB"
echo "  CPU Cores: $CPU_CORES"
echo ""

# Calculate recommended models based on VRAM
if [ "$TOTAL_VRAM" -ge 46000 ]; then
    # Dual 24GB GPUs or similar - can run everything
    CONFIG_PROFILE="peak"
    info "Recommended profile: PEAK (all 9 models)"
elif [ "$TOTAL_VRAM" -ge 20000 ]; then
    # Single 24GB GPU - can run most models
    CONFIG_PROFILE="high"
    info "Recommended profile: HIGH (7 models, skip video generation)"
elif [ "$TOTAL_VRAM" -ge 12000 ]; then
    # 12-16GB GPU - medium setup
    CONFIG_PROFILE="medium"
    info "Recommended profile: MEDIUM (5 models, smaller LLMs)"
elif [ "$TOTAL_VRAM" -ge 6000 ]; then
    # 6-8GB GPU - basic setup
    CONFIG_PROFILE="basic"
    info "Recommended profile: BASIC (3 models, 4B/7B LLMs only)"
else
    # CPU-only or very limited GPU
    CONFIG_PROFILE="cpu"
    info "Recommended profile: CPU (2 small models, quantized)"
fi

echo ""
read -p "Use recommended profile ($CONFIG_PROFILE)? [Y/n/profile_name] " USE_PROFILE
USE_PROFILE=${USE_PROFILE:-Y}

if [[ ! "$USE_PROFILE" =~ ^[Yy]$ ]]; then
    if [[ "$USE_PROFILE" =~ ^(peak|high|medium|basic|cpu)$ ]]; then
        CONFIG_PROFILE="$USE_PROFILE"
        info "Using profile: $CONFIG_PROFILE"
    else
        error "Invalid profile. Use: peak, high, medium, basic, or cpu"
        exit 1
    fi
fi

# Step 2: Create directory structure
log "Creating directory structure..."
mkdir -p "$HOME_DIR"/{logs,models,config,data}
mkdir -p "$ROOT_DIR/bin"
success "Directories created at $HOME_DIR"

# Step 3: Install TailScale (optional but recommended)
echo ""
read -p "Install/configure TailScale for remote access? [Y/n] " INSTALL_TAILSCALE
INSTALL_TAILSCALE=${INSTALL_TAILSCALE:-Y}

if [[ "$INSTALL_TAILSCALE" =~ ^[Yy]$ ]]; then
    log "Setting up TailScale..."
    
    # Check if already installed
    if command -v tailscale >/dev/null 2>&1; then
        info "TailScale already installed"
        
        # Check if running
        if ! pgrep -x "tailscaled" >/dev/null 2>&1; then
            read -p "Start TailScale service? [Y/n] " START_TS
            if [[ "$START_TS" =~ ^[Yy]$ ]]; then
                sudo systemctl start tailscaled || sudo service tailscale start || warn "Could not start TailScale"
                sudo systemctl enable tailscaled 2>/dev/null || true
            fi
        fi
        
        # Get TailScale IP
        TAILSCALE_IP=$(tailscale ip 2>/dev/null || echo "")
        if [ -n "$TAILSCALE_IP" ]; then
            success "TailScale IP: $TAILSCALE_IP"
        else
            warn "Could not get TailScale IP. Make sure you're logged in."
        fi
    else
        log "Installing TailScale..."
        
        # Download and install TailScale
        curl -fsSL https://tailscale.com/install.sh | sh
        
        # Start service
        sudo systemctl enable --now tailscaled
        
        success "TailScale installed"
        info "Run 'tailscale up' to connect to your TailScale network"
        
        read -p "Open authorization URL now? [y/N] " AUTH_TS
        if [[ "$AUTH_TS" =~ ^[Yy]$ ]]; then
            TAILSCALE_URL=$(curl -s https://login.tailscale.com/a/$(cat /var/lib/tailscale/authkey 2>/dev/null || tailscale login --qr 2>&1 | grep -oP 'https://[\w./-]*' | head -1) || echo "Run: tailscale up")
            info "Authorize at: $TAILSCALE_URL"
        fi
    fi
else
    warn "Skipping TailScale installation. Remote access will not be available."
fi

# Step 4: Install system dependencies
log "Checking system dependencies..."

# Check for NVIDIA drivers and CUDA
if [ "$GPU_COUNT" -gt 0 ]; then
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        error "NVIDIA GPU detected but nvidia-smi not found!"
        error "Install NVIDIA drivers first: https://docs.nvidia.com/datacenter/tesla/index.html"
        exit 1
    fi
    success "NVIDIA drivers verified"
    
    # Check CUDA toolkit (optional for llama.cpp)
    if ! command -v nvcc >/dev/null 2>&1; then
        warn "CUDA toolkit not found. llama.cpp will use built-in CUDA."
        info "For optimal performance, install CUDA 11.8+: https://developer.nvidia.com/cuda-toolkit"
    fi
fi

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
    error "Python 3 is required but not installed"
    exit 1
fi
success "Python 3: $(python3 --version)"

# Check for required tools
MISSING_DEPS=()
for dep in git curl wget make cmake; do
    if ! command -v $dep >/dev/null 2>&1; then
        MISSING_DEPS+=($dep)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log "Installing missing dependencies: ${MISSING_DEPS[*]}"
    
    # Detect package manager
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y "${MISSING_DEPS[@]}" build-essential
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y "${MISSING_DEPS[@]}" gcc make cmake
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm "${MISSING_DEPS[@]}" base-devel
    else
        error "Unsupported package manager. Install manually: ${MISSING_DEPS[*]}"
        exit 1
    fi
    success "Dependencies installed"
fi

# Step 5: Build llama.cpp
log "Building llama.cpp (this may take 5-20 minutes)..."

LLAMA_CPP_DIR="$HOME_DIR/llama.cpp"
if [ -d "$LLAMA_CPP_DIR/.git" ]; then
    info "llama.cpp already exists, updating..."
    cd "$LLAMA_CPP_DIR"
    git pull
else
    log "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP_DIR"
fi

cd "$LLAMA_CPP_DIR"

# Build with appropriate flags
BUILD_FLAGS="-DGGML_BUILD=ON -DCMAKE_BUILD_TYPE=Release"

if [ "$GPU_COUNT" -gt 0 ]; then
    BUILD_FLAGS="$BUILD_FLAGS -DGGML_CUDA=ON"
    info "Building with CUDA support"
else
    BUILD_FLAGS="$BUILD_FLAGS -DGGML_BLAS=ON"
    info "Building with CPU optimizations (BLAS)"
fi

# Create build directory and compile
mkdir -p build
cd build
cmake $BUILD_FLAGS .. 2>&1 | tail -20
make -j$(nproc) 2>&1 | tail -30

success "llama.cpp built successfully"

# Copy binaries to Senter-Server bin directory
cp llama-server "$ROOT_DIR/bin/"
success "llama-server copied to $ROOT_DIR/bin/"

# Step 6: Install Python dependencies
log "Installing Python dependencies..."

cd "$ROOT_DIR"
pip3 install -q uvicorn fastapi requests aiohttp python-multipart

success "Python dependencies installed"

# Step 7: Generate configuration file
log "Generating configuration..."

cat > "$HOME_DIR/config/server.conf" << EOF
# Senter Server Configuration
# Generated: $(date)
# Profile: $CONFIG_PROFILE

# Hardware
GPU_COUNT=$GPU_COUNT
TOTAL_VRAM=$TOTAL_VRAM
CPU_CORES=$CPU_CORES

# Network
TAILSCALE_IP=${TAILSCALE_IP:-100.84.195.22}
SERVER_HOST=0.0.0.0

# Ports
PORT_LLM=8100
PORT_IMAGE=8108
PORT_IMAGE_EDIT=8109
PORT_TTS=8102
PORT_ACESTEP=8106
PORT_LTX=8105

# Paths
MODELS_DIR="$HOME_DIR/models"
LOG_DIR="$HOME_DIR/logs"
BIN_DIR="$ROOT_DIR/bin"

# Profile Settings
CONFIG_PROFILE=$CONFIG_PROFILE

# Model Selection (based on profile)
EOF

success "Configuration saved to $HOME_DIR/config/server.conf"

# Step 8: Create model download scripts
log "Creating model download scripts..."

cp "$SCRIPT_DIR/downloads/"*.sh "$ROOT_DIR/scripts/" 2>/dev/null || true
chmod +x "$ROOT_DIR/scripts/download-"*.sh 2>/dev/null || true

success "Download scripts ready"

# Step 9: Update PATH
log "Updating your shell configuration..."

if ! grep -q "Senter-Server/bin" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Senter Server" >> ~/.bashrc
    echo 'export PATH="$PATH:'"$ROOT_DIR"'/bin"' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:'"$ROOT_DIR"'/bin"' >> ~/.bashrc
    success "Added to ~/.bashrc - run 'source ~/.bashrc' to apply"
else
    info "PATH already configured"
fi

# Step 10: Summary and next steps
echo ""
echo "========================================"
success "Senter Server Installation Complete!"
echo "========================================"
echo ""
info "Configuration:"
echo "  Profile: $CONFIG_PROFILE"
echo "  Install location: $ROOT_DIR"
echo "  Config directory: $HOME_DIR"
echo "  TailScale IP: ${TAILSCALE_IP:-Not configured}"
echo ""
info "Next steps:"
echo "  1. Source your shell: source ~/.bashrc"
echo "  2. Download models: ./scripts/download-models.sh $CONFIG_PROFILE"
echo "  3. Start services: model-server start qwen35"
echo "  4. Check status: model-server status"
echo ""
info "Available commands:"
echo "  model-server list        # Show all available models"
echo "  model-server start <model>  # Start a specific model"
echo "  model-server status      # Check running services"
echo "  model-server stop        # Stop all services"
echo ""
success "You're ready to go! See README.md for full documentation."