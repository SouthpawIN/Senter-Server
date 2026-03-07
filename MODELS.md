# Model Specifications 📊

Complete reference for all models supported by Senter Server.

---

## LLM Models (Port 8100)

All LLMs use the same endpoint with automatic model switching. Only one LLM can run at a time due to VRAM constraints.

### Qwen3.5-35B-A3B (1M Context)

**Best for**: Long documents, full codebases, extensive context

| Property | Value |
|----------|-------|
| Parameters | 35B |
| Quantization | Q4_K_XL |
| File Size | ~22GB |
| VRAM Required | ~26GB (dual GPU recommended) |
| Context Window | 1,000,000 tokens |
| Speed | ~40-50 tokens/sec |
| RoPE Scaling | YaRN (4x scale, orig ctx 262K) |

**Download**:
```bash
./scripts/download-models.sh peak
```

**HuggingFace**: https://huggingface.co/Qwen/Qwen3.5-35B-A3B-GGUF

**Usage**:
```bash
senter-server start qwen35-1m
```

**Configuration**:
```bash
--ctx-size 1010000
--rope-scaling yarn
--rope-scale 4.0
--yarn-orig-ctx 262144
--cache-type-k q4_0
--cache-type-v q4_0
```

---

### Qwen3.5-35B-A3B (Standard)

**Best for**: General reasoning, balanced performance

| Property | Value |
|----------|-------|
| Parameters | 35B |
| Quantization | Q4_K_XL |
| File Size | ~22GB |
| VRAM Required | ~26GB |
| Context Window | 262,144 tokens |
| Speed | ~80 tokens/sec |

**Download**: Same file as 1M version

**Usage**:
```bash
senter-server start qwen35
```

**Configuration**:
```bash
--ctx-size 262144
--cache-type-k q8_0
--cache-type-v q8_0
--threads 10
```

---

### Qwen3.5-27B

**Best for**: Alternative reasoning, slightly faster inference

| Property | Value |
|----------|-------|
| Parameters | 27B |
| Quantization | Q6_K |
| File Size | ~17GB |
| VRAM Required | ~20GB |
| Context Window | 262,144 tokens |
| Speed | ~60-70 tokens/sec |

**Download**:
```bash
./scripts/download-models.sh peak
```

**HuggingFace**: https://huggingface.co/Qwen/Qwen3.5-27B-GGUF

**Usage**:
```bash
senter-server start qwen27
```

---

### Qwen2.5-Omni-3B (Multimodal)

**Best for**: Vision understanding, audio processing, multimodal tasks

| Property | Value |
|----------|-------|
| Parameters | 3B |
| Quantization | Q4_K_M (model), Q8_0 (mmproj) |
| File Size | ~4GB total |
| VRAM Required | ~6GB |
| Context Window | 8,192 tokens |
| Speed | ~100+ tokens/sec |
| Capabilities | Vision, Audio, Text |

**Files**:
- `Qwen2.5-Omni-3B-Q4_K_M.gguf` (~3GB)
- `mmproj-Qwen2.5-Omni-3B-Q8_0.gguf` (~1GB)

**Download**:
```bash
./scripts/download-models.sh medium  # or higher
```

**HuggingFace**: https://huggingface.co/Qwen/Qwen2.5-Omni-3B-GGUF

**Usage**:
```bash
senter-server start qwen-omni
```

**Multimodal Input Example**:
```json
{
  "messages": [{
    "role": "user",
    "content": [
      {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}},
      {"type": "text", "text": "Describe this image."}
    ]
  }]
}
```

---

### Qwen2.5-7B-Instruct (Limited VRAM)

**Best for**: Systems with 8-12GB VRAM

| Property | Value |
|----------|-------|
| Parameters | 7B |
| Quantization | Q4_K_M |
| File Size | ~5GB |
| VRAM Required | ~7GB |
| Context Window | 32,768 tokens |
| Speed | ~120+ tokens/sec |

**Download**: Included in MEDIUM profile

**HuggingFace**: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

---

### Qwen2.5-3B-Instruct (CPU/BASIC)

**Best for**: CPU-only or very limited VRAM (<6GB)

| Property | Value |
|----------|-------|
| Parameters | 3B |
| Quantization | Q4_K_M |
| File Size | ~2GB |
| VRAM Required | ~4GB (or CPU RAM) |
| Context Window | 8,192 tokens |
| Speed | ~50-80 tok/s (GPU), ~5-10 tok/s (CPU) |

**Download**: Included in all profiles

**HuggingFace**: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF

---

## Specialized Services

### Soprano 80M (TTS) - Port 8102

**Best for**: Text-to-speech synthesis, voice responses

| Property | Value |
|----------|-------|
| Type | Python Package |
| Size | ~100MB |
| VRAM | Negligible |
| Speed | Real-time |
| Voices | Multiple options |

**Installation**:
```bash
pip3 install soprano-tts
```

**Usage**:
```bash
senter-server start soprano
```

**API**:
```bash
curl -X POST http://localhost:8102/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "voice": "default"}' \
  -o output.wav
```

---

### Qwen Image Generation - Port 8108

**Best for**: Text-to-image creation

| Property | Value |
|----------|-------|
| Type | FastAPI Server |
| Recommended Model | flux.1-schnell or SD3 |
| VRAM Required | 8GB+ |
| Status | Placeholder (implement with preferred model) |

**Usage**:
```bash
senter-server start qwen-image
```

**Note**: Current implementation is a placeholder. Install your preferred image generation model:
- flux.1-schnell (fast, high quality)
- stable-diffusion-3-medium
- qwen-image (if available)

---

### Qwen Image Edit - Port 8109

**Best for**: Image modification, inpainting, outpainting

| Property | Value |
|----------|-------|
| Type | FastAPI Server |
| VRAM Required | 8GB+ |
| Status | Placeholder |

**Usage**:
```bash
senter-server start qwen-edit
```

---

### LTX-Video - Port 8105

**Best for**: Text-to-video generation

| Property | Value |
|----------|-------|
| Parameters | 2B |
| VRAM Required | 12GB+ |
| Context | Video frames |
| Speed | ~1-5 fps (generation) |

**Installation**:
```bash
./scripts/download-models.sh peak  # Only in PEAK profile
```

**Repository**: https://github.com/Lightricks/LTX-Video

**Usage**:
```bash
senter-server start ltx
```

---

### AceStep - Port 8106

**Best for**: Music generation, audio synthesis

| Property | Value |
|----------|-------|
| Parameters | 1.5B |
| VRAM Required | 6GB+ |
| Output | Audio files (WAV/MP3) |
| Status | Placeholder |

**Usage**:
```bash
senter-server start acestep
```

**Note**: Current implementation is a placeholder. Install AceStep LoRA for full functionality.

---

## Profile Recommendations

### PEAK Profile (48GB+ VRAM)
All 9 models:
- Qwen3.5-35B-A3B (both modes)
- Qwen3.5-27B
- Qwen2.5-Omni-3B
- Soprano TTS
- Image Generation
- Image Edit
- LTX-Video
- AceStep Music

**Total Download**: ~60GB
**VRAM Usage**: Up to 46GB (not all at once)

### HIGH Profile (20-24GB VRAM)
7 models (no video):
- All PEAK except LTX-Video

**Total Download**: ~45GB

### MEDIUM Profile (12-16GB VRAM)
5 models:
- Qwen2.5-7B or Qwen2.5-3B
- Qwen2.5-Omni-3B
- Soprano TTS
- (No image/video/music generation)

**Total Download**: ~10GB

### BASIC Profile (6-8GB VRAM)
3 models:
- Qwen2.5-3B
- Soprano TTS
- (Minimal setup)

**Total Download**: ~5GB

### CPU Profile (<6GB VRAM or CPU-only)
2 models:
- Qwen2.5-3B (CPU inference)
- Soprano TTS

**Total Download**: ~3GB
**Performance**: Slow but functional

---

## Model Switching Guide

### When to Use Each LLM

| Task | Recommended Model | Reason |
|------|------------------|--------|
| Analyzing full codebase | qwen35-1m | 1M context fits entire project |
| Reading long documents | qwen35-1m | Can process books/reports |
| General conversation | qwen35 | Best speed/quality balance |
| Complex reasoning | qwen35 or qwen27 | Both excellent at logic |
| Vision tasks | qwen-omni | Only multimodal option |
| Audio understanding | qwen-omni | Processes speech directly |
| Limited resources | qwen2.5-7B/3B | Smaller, faster |

### Switching Commands

```bash
# Stop current model and start new one
senter-server start qwen35-1m  # Automatically switches

# Or manually
senter-server stop
sleep 2
senter-server start qwen-omni
```

---

## Download Sources

### Primary: HuggingFace

All Qwen models are hosted on official HuggingFace repositories:
- https://huggingface.co/Qwen

### Alternative: Model Repositories

If HuggingFace is slow/unavailable:
- https://civitai.com (some models)
- https://huggingface.co/microsoft (mirrors)
- Local sharing via TailScale

### Manual Download

For advanced users, download directly:
```bash
# Example for Qwen3.5-35B
wget https://huggingface.co/Qwen/Qwen3.5-35B-A3B-GGUF/resolve/main/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf \
  -P ~/.senter-server/models/Qwen3.5-35B-A3B-GGUF/
```

---

## Performance Benchmarks

Tested on dual RTX 3090 (2x24GB VRAM):

| Model | Tokens/Sec | Time to First Token | VRAM Used |
|-------|------------|---------------------|-----------|
| Qwen3.5-35B-A3B (1M) | 40-50 | ~500ms | 26GB |
| Qwen3.5-35B-A3B | 75-85 | ~300ms | 26GB |
| Qwen3.5-27B | 60-70 | ~400ms | 20GB |
| Qwen2.5-Omni-3B | 100-120 | ~200ms | 6GB |
| Qwen2.5-7B | 120-150 | ~150ms | 7GB |
| Qwen2.5-3B | 150-200 | ~100ms | 4GB |

*Note: Performance varies with prompt length and system load.*

---

## Optimization Tips

### For Speed
- Use smaller models (3B, 7B)
- Reduce context window if not needed
- Increase `--threads` for CPU fallback
- Use `--flash-attn on` for GPU

### For Quality
- Use larger models (27B, 35B)
- Q6_K quantization over Q4_K
- Higher temperature for creativity (0.8-1.0)
- Lower temperature for precision (0.3-0.5)

### For VRAM Efficiency
- Use q4_0 cache types
- Reduce context window
- Close other GPU applications
- Consider CPU offload for very large contexts

---

## Update History

### March 2026 (Current)
- Added Qwen3.5-35B-A3B with 1M context support
- Implemented YaRN scaling for ultra-long contexts
- Added profile-based model selection
- Integrated all 9 services into unified manager

### Future Plans
- Add more specialized models (coding, math)
- Support for LoRA adapters
- Model fine-tuning pipeline
- Automatic model updates from HuggingFace

---

*Last updated: March 7, 2026 | Maintained by SouthpawIN*