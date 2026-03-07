#!/bin/bash
# Model Download Script for Senter Server
# Downloads models based on configuration profile
# Profiles: peak, high, medium, basic, cpu

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOME_DIR="${HOME}/.senter-server"

# Load configuration
if [ -f "$HOME_DIR/config/server.conf" ]; then
    source "$HOME_DIR/config/server.conf"
fi

MODELS_DIR="${MODELS_DIR:-$HOME_DIR/models}"
CONFIG_PROFILE="${CONFIG_PROFILE:-medium}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[Download]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
info() { echo -e "${CYAN}ℹ${NC} $1"; }

echo "========================================"
echo "  Model Download Manager"
echo "  Profile: $CONFIG_PROFILE"
echo "========================================"
echo ""

# Create models directory
mkdir -p "$MODELS_DIR"

# Function to check if file exists and is valid
check_model() {
    local model_path=$1
    local min_size=${2:-100000000}  # Default 100MB minimum
    
    if [ -f "$model_path" ]; then
        local size=$(stat -f%z "$model_path" 2>/dev/null || stat -c%s "$model_path" 2>/dev/null)
        if [ "$size" -gt "$min_size" ]; then
            return 0  # File exists and is large enough
        fi
    fi
    return 1
}

# Function to download with progress (using wget or curl)
download_file() {
    local url=$1
    local output=$2
    local name=$3
    
    info "Downloading $name..."
    info "URL: $url"
    
    mkdir -p "$(dirname "$output")"
    
    if command -v aria2c >/dev/null 2>&1; then
        # Use aria2c for fastest downloads with resume support
        aria2c -x 16 -s 16 -k 1M --continue --file-allocation=none "$url" -d "$(dirname "$output")" -o "$(basename "$output")"
    elif command -v wget >/dev/null 2>&1; then
        wget --continue --show-progress "$url" -O "$output"
    else
        curl -#L "$url" -o "$output"
    fi
    
    if [ -f "$output" ]; then
        success "$name downloaded successfully"
        return 0
    else
        error "Download failed for $name"
        return 1
    fi
}

# Model download functions by category

download_qwen35_35b() {
    log "Downloading Qwen3.5-35B-A3B (35B parameter model, ~22GB)..."
    
    local model_path="$MODELS_DIR/Qwen3.5-35B-A3B-GGUF/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf"
    
    if check_model "$model_path"; then
        success "Qwen3.5-35B already present"
        return 0
    fi
    
    mkdir -p "$MODELS_DIR/Qwen3.5-35B-A3B-GGUF"
    
    # HuggingFace URL (using a reliable mirror or direct link)
    local url="https://huggingface.co/Qwen/Qwen3.5-35B-A3B-GGUF/resolve/main/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf"
    
    download_file "$url" "$model_path" "Qwen3.5-35B-A3B Q4_K_XL"
}

download_qwen35_1m() {
    log "Downloading Qwen3.5-35B-A3B 1M Context (same model, different config)..."
    
    # Same model file as qwen35, just used with different context settings
    local model_path="$MODELS_DIR/Qwen3.5-35B-A3B-GGUF/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf"
    
    if check_model "$model_path"; then
        success "Qwen3.5-35B already present (used for both qwen35 and qwen35-1m)"
        return 0
    fi
    
    download_qwen35_35b
}

download_qwen27() {
    log "Downloading Qwen3.5-27B (27B parameter model, ~17GB)..."
    
    local model_path="$MODELS_DIR/Qwen3.5-27B-GGUF/Qwen3.5-27B-Q6_K.gguf"
    
    if check_model "$model_path"; then
        success "Qwen3.5-27B already present"
        return 0
    fi
    
    mkdir -p "$MODELS_DIR/Qwen3.5-27B-GGUF"
    
    local url="https://huggingface.co/Qwen/Qwen3.5-27B-GGUF/resolve/main/Qwen3.5-27B-Q6_K.gguf"
    download_file "$url" "$model_path" "Qwen3.5-27B Q6_K"
}

download_qwen_omni() {
    log "Downloading Qwen2.5-Omni-3B (multimodal vision/audio, ~4GB)..."
    
    local model_dir="$MODELS_DIR/Qwen2.5-Omni-3B-GGUF"
    local model_path="$model_dir/Qwen2.5-Omni-3B-Q4_K_M.gguf"
    local mmproj_path="$model_dir/mmproj-Qwen2.5-Omni-3B-Q8_0.gguf"
    
    mkdir -p "$model_dir"
    
    # Download model
    if ! check_model "$model_path"; then
        local url="https://huggingface.co/Qwen/Qwen2.5-Omni-3B-GGUF/resolve/main/Qwen2.5-Omni-3B-Q4_K_M.gguf"
        download_file "$url" "$model_path" "Qwen2.5-Omni-3B model"
    else
        success "Qwen2.5-Omni-3B model already present"
    fi
    
    # Download mmproj
    if ! check_model "$mmproj_path"; then
        local url="https://huggingface.co/Qwen/Qwen2.5-Omni-3B-GGUF/resolve/main/mmproj-Qwen2.5-Omni-3B-Q8_0.gguf"
        download_file "$url" "$mmproj_path" "Qwen2.5-Omni mmproj"
    else
        success "Qwen2.5-Omni mmproj already present"
    fi
}

download_qwen_small() {
    log "Downloading smaller Qwen models for limited VRAM..."
    
    # Qwen2.5-7B (good balance, ~5GB)
    local model_7b="$MODELS_DIR/Qwen2.5-7B-GGUF/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    if ! check_model "$model_7b"; then
        mkdir -p "$MODELS_DIR/Qwen2.5-7B-GGUF"
        download_file \
            "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf" \
            "$model_7b" \
            "Qwen2.5-7B-Instruct"
    else
        success "Qwen2.5-7B already present"
    fi
    
    # Qwen2.5-3B (very small, ~2GB)
    local model_3b="$MODELS_DIR/Qwen2.5-3B-GGUF/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
    if ! check_model "$model_3b"; then
        mkdir -p "$MODELS_DIR/Qwen2.5-3B-GGUF"
        download_file \
            "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf" \
            "$model_3b" \
            "Qwen2.5-3B-Instruct"
    else
        success "Qwen2.5-3B already present"
    fi
}

download_soprano() {
    log "Installing Soprano TTS (text-to-speech)..."
    
    # Soprano is a Python package
    if python3 -c "import soprano" 2>/dev/null; then
        success "Soprano already installed"
        return 0
    fi
    
    pip3 install -q soprano-tts
    success "Soprano TTS installed"
}

download_image_models() {
    log "Setting up image generation models..."
    
    # For Qwen image generation, we need FLUX or similar
    # Using a smaller, faster model for demo purposes
    
    info "Image generation requires additional setup"
    info "For production use, consider installing: flux.1-schnell, stable-diffusion-3, or qwen-image"
    
    # Create placeholder scripts
    cat > "$ROOT_DIR/bin/qwen-image-server.py" << 'IMAGE_SERVER'
#!/usr/bin/env python3
"""Placeholder Qwen Image Generation Server"""
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/v1/health")
def health():
    return {"status": "ok", "model": "qwen-image"}

@app.post("/v1/images/generations")
def generate_image(prompt: str = "", size: str = "1024x1024"):
    # Placeholder - implement with actual image generation model
    return {
        "status": "placeholder",
        "message": "Install flux.1 or stable-diffusion for actual image generation",
        "prompt": prompt,
        "size": size
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8108)
IMAGE_SERVER
    chmod +x "$ROOT_DIR/bin/qwen-image-server.py"
    
    cat > "$ROOT_DIR/bin/qwen-image-edit-server.py" << 'EDIT_SERVER'
#!/usr/bin/env python3
"""Placeholder Qwen Image Edit Server"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/v1/health")
def health():
    return {"status": "ok", "model": "qwen-edit"}

@app.post("/v1/images/edits")
def edit_image(image: str = "", prompt: str = ""):
    return {
        "status": "placeholder", 
        "message": "Install image editing model for actual functionality"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8109)
EDIT_SERVER
    chmod +x "$ROOT_DIR/bin/qwen-image-edit-server.py"
    
    success "Image server placeholders created"
}

download_video_model() {
    log "Setting up LTX-Video (video generation)..."
    
    LTX_DIR="$HOME_DIR/LTX-Video-original"
    
    if [ -d "$LTX_DIR/.git" ]; then
        success "LTX-Video already cloned"
        return 0
    fi
    
    # Clone LTX-Video repository
    git clone https://github.com/Lightricks/LTX-Video.git "$LTX_DIR"
    
    # Create virtual environment
    cd "$LTX_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118
    pip install -q -r requirements.txt
    
    success "LTX-Video installed"
}

download_music_model() {
    log "Setting up AceStep (music generation)..."
    
    # Create placeholder for now
    cat > "$ROOT_DIR/bin/acestep-lora-pipeline.py" << 'MUSIC_PIPELINE'
#!/usr/bin/env python3
"""Placeholder AceStep Music Generation Pipeline"""
import argparse
from fastapi import FastAPI

app = FastAPI()

@app.get("/v1/health")
def health():
    return {"status": "ok", "model": "acestep"}

@app.post("/v1/audio/generations")
def generate_music(prompt: str = "", duration: int = 30):
    return {
        "status": "placeholder",
        "message": "Install AceStep LoRA for actual music generation",
        "prompt": prompt,
        "duration": duration
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--port", type=int, default=8106)
    args = parser.parse_args()
    
    if args.server:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=args.port)
MUSIC_PIPELINE
    chmod +x "$ROOT_DIR/bin/acestep-lora-pipeline.py"
    
    success "AceStep placeholder created"
    info "For full music generation, install AceStep LoRA separately"
}

# Profile-based download functions

download_peak() {
    log "Downloading PEAK profile (all 9 models)..."
    echo ""
    
    download_qwen35_35b
    echo ""
    download_qwen27
    echo ""
    download_qwen_omni
    echo ""
    download_soprano
    echo ""
    download_image_models
    echo ""
    download_video_model
    echo ""
    download_music_model
}

download_high() {
    log "Downloading HIGH profile (7 models, no video)..."
    echo ""
    
    download_qwen35_35b
    echo ""
    download_qwen27
    echo ""
    download_qwen_omni
    echo ""
    download_soprano
    echo ""
    download_image_models
    echo ""
    download_music_model
    
    warn "Skipping LTX-Video (requires 24GB+ VRAM)"
}

download_medium() {
    log "Downloading MEDIUM profile (5 models, smaller LLMs)..."
    echo ""
    
    download_qwen_small  # 7B and 3B instead of 27B/35B
    echo ""
    download_qwen_omni
    echo ""
    download_soprano
    echo ""
    warn "Skipping image/video/music generation (requires significant VRAM)"
}

download_basic() {
    log "Downloading BASIC profile (3 models, minimal VRAM)..."
    echo ""
    
    download_qwen_small  # Just the small models
    echo ""
    download_soprano
    
    warn "Skipping multimodal and generation models"
}

download_cpu() {
    log "Downloading CPU profile (2 smallest models)..."
    echo ""
    
    # Download only the smallest Qwen model
    local model_3b="$MODELS_DIR/Qwen2.5-3B-GGUF/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
    if ! check_model "$model_3b"; then
        mkdir -p "$MODELS_DIR/Qwen2.5-3B-GGUF"
        download_file \
            "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf" \
            "$model_3b" \
            "Qwen2.5-3B-Instruct"
    else
        success "Qwen2.5-3B already present"
    fi
    
    echo ""
    download_soprano
    
    warn "CPU-only mode - will be slow but functional"
}

# Main execution
case "$CONFIG_PROFILE" in
    peak)  download_peak ;;
    high)  download_high ;;
    medium) download_medium ;;
    basic) download_basic ;;
    cpu)   download_cpu ;;
    *)
        error "Unknown profile: $CONFIG_PROFILE"
        echo "Valid profiles: peak, high, medium, basic, cpu"
        exit 1
        ;;
esac

echo ""
echo "========================================"
success "Model download complete!"
echo "========================================"
echo ""
info "Your models are ready at: $MODELS_DIR"
echo ""
log "Starting a model:"
echo "  model-server start qwen35    # For PEAK/HIGH profiles"
echo "  model-server start qwen27    # For PEAK/HIGH profiles"  
echo "  model-server start qwen-omni # For most profiles"
echo ""
echo "  model-server status          # Check what's running"