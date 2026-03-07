#!/bin/bash
# Hardware Detection Script for Senter Server
# Detects GPU count, VRAM, and CPU cores

# Detect NVIDIA GPUs
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
    
    if [ "$GPU_COUNT" -gt 0 ]; then
        # Get total VRAM across all GPUs (in MB)
        TOTAL_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | awk -F',' '{sum += $1} END {print sum}')
        TOTAL_VRAM=${TOTAL_VRAM:-0}
        
        # Get individual GPU info
        echo "Detected NVIDIA GPUs:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | while read line; do
            echo "  $line"
        done
        
        # Check for multi-GPU setup
        if [ "$GPU_COUNT" -gt 1 ]; then
            echo ""
            echo "Multi-GPU configuration detected!"
            echo "llama.cpp will automatically distribute layers across GPUs"
        fi
    else
        GPU_COUNT=0
        TOTAL_VRAM=0
    fi
else
    GPU_COUNT=0
    TOTAL_VRAM=0
    echo "No NVIDIA GPU detected or nvidia-smi not available"
fi

# Detect CPU cores
CPU_CORES=$(nproc 2>/dev/null || echo 4)

# Check RAM
if [ -f /proc/meminfo ]; then
    SYSTEM_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
else
    SYSTEM_RAM=0
fi

echo ""
echo "Hardware Summary:"
echo "  GPU Count: $GPU_COUNT"
echo "  Total VRAM: ${TOTAL_VRAM}MB"
echo "  CPU Cores: $CPU_CORES"
[ "$SYSTEM_RAM" -gt 0 ] && echo "  System RAM: ${SYSTEM_RAM}KB"

# Export variables for use in other scripts
export GPU_COUNT
export TOTAL_VRAM
export CPU_CORES
export SYSTEM_RAM