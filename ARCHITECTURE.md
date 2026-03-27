Senter-Server Architecture
==========================

Overview
--------
Senter-Server is an AI inference server that provides:
- Text model endpoints (chat/completions)
- Vision model endpoints (image analysis)
- MCP (Model Context Protocol) server integration

API Endpoints
-------------
Text Model:   POST /api/v1/chat/completions
Vision Model: POST /api/v1/images/analyze
Hermes Reason: POST /api/hermes/reason

MCP Configuration
-----------------
The MCP server exposes these capabilities:
- text_model: Primary LLM for chat/completions
- vision_model: Multimodal model for image analysis
- reasoning: Advanced reasoning endpoint via Hermes interface
