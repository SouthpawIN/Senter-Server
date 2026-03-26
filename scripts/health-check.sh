#!/bin/bash
# Senter-Server Health Check - Quick status of all model endpoints

ENDPOINTS=("8100:Qwen-LLM" "8101:Qwen-Omni" "8102:Soprano-TTS" "8105:LTX-Video" "8106:AceStep" "8108:Image-Gen" "8109:Image-Edit")
RED='\033[0;31m' GREEN='\033[0;32m' NC='\033[0m'

echo -e "${GREEN}=== Senter-Server Health Check ===${NC}"
printf "%-6s | %-15s | %-4s | %s\n" "PORT" "SERVICE" "STAT" "CODE"
echo "------|-----------------|------|-------"

overall="HEALTHY"
for entry in "${ENDPOINTS[@]}"; do
    IFS=':' read -r port name <<< "$entry"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:${port}/health" 2>/dev/null || echo "000")
    if [[ "$code" =~ ^[23][0-9]{2}$ ]]; then
        printf "%-6s | %-15s | ${GREEN}UP${NC}   | %s\n" "$port" "$name" "$code"
    else
        printf "%-6s | %-15s | ${RED}DOWN${NC}  | %s\n" "$port" "$name" "$code"
        overall="DEGRADED"
    fi
done

if command -v nvidia-smi &>/dev/null; then
    echo ""
    echo -e "VRAM: $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null | awk -F, '{u+=$1;t+=$2}END{printf "%dMB/%dMB (%d%%)",u,t,u*100/t}')" 
fi
echo ""
echo -e "Status: ${overall == 'HEALTHY' && echo -e \"${GREEN}HEALTHY${NC}\" || echo -e \"${RED}DEGRADED${NC}\"}"
[[ "$overall" == "HEALTHY" ]] && exit 0 || exit 1
