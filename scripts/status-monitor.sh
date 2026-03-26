#!/bin/bash
# Senter-Server Status Monitor - Continuous monitoring with multiple modes

ENDPOINTS=("8100:Qwen-LLM" "8101:Qwen-Omni" "8102:Soprano-TTS" "8105:LTX-Video" "8106:AceStep" "8108:Image-Gen" "8109:Image-Edit")
RED='\033[0;31m' GREEN='\033[0;32m' BLUE='\033[0;34m' CYAN='\033[0;36m' NC='\033[0m'

print_status() {
    echo -e "${BLUE}=== Senter-Server Status ===${NC} $(date '+%H:%M:%S')"
    printf "%-6s | %-15s | %s\n" "PORT" "SERVICE" "STATUS"
    echo "------|-----------------|--------"
    local up=0 down=0
    for entry in "${ENDPOINTS[@]}"; do
        IFS=':' read -r port name <<< "$entry"
        if timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1; then
            printf "%-6s | %-15s | ${GREEN}UP${NC}\n" "$port" "$name"; ((up++))
        else
            printf "%-6s | %-15s | ${RED}DOWN${NC}\n" "$port" "$name"; ((down++))
        fi
    done
    echo ""
    echo -e "Summary: ${GREEN}$up UP${NC}, ${RED}$down DOWN${NC}"
}

case "${1:-status}" in
    status|s) print_status ;;
    monitor|m)
        interval=${2:-30}
        echo -e "${BLUE}Monitoring every ${interval}s (Ctrl+C to stop)${NC}"
        while true; do clear; print_status; sleep "$interval"; done
        ;;
    alert|a)
        echo -e "${BLUE}Alert mode - monitoring for changes...${NC}"
        declare -A prev
        for entry in "${ENDPOINTS[@]}"; do
            IFS=':' read -r port name <<< "$entry"
            [[ $(timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1 && echo 1 || echo 0) == "1" ]] && prev[$port]=1 || prev[$port]=0
        done
        while true; do
            for entry in "${ENDPOINTS[@]}"; do
                IFS=':' read -r port name <<< "$entry"
                cur=$(timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1 && echo 1 || echo 0)
                if [[ "$cur" != "${prev[$port]}" ]]; then
                    ts=$(date '+%Y-%m-%d %H:%M:%S')
                    if [[ "$cur" == "1" ]]; then
                        echo -e "${GREEN}[$ts] UP: $name (:$port)${NC}"
                    else
                        echo -e "${RED}[$ts] DOWN: $name (:$port)${NC}"
                    fi
                    prev[$port]=$cur
                fi
            done
            sleep 10
        done
        ;;
    json|j)
        echo "{\"timestamp\": \"$(date -Iseconds)\", \"services\": {"
        first=true; up=0; down=0
        for entry in "${ENDPOINTS[@]}"; do
            IFS=':' read -r port name <<< "$entry"
            cur=$(timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1 && echo "up" || echo "down")
            [[ "$cur" == "up" ]] && ((up++)) || ((down++))
            [[ "$first" == "true" ]] && first=false || echo ","
            printf '    "%s": {"port": %d, "status": "%s"}' "$name" "$port" "$cur"
        done
        echo -e "\n  }, \"summary\": {\"up\": $up, \"down\": $down}}"
        ;;
    *) echo "Usage: $0 {status|monitor [interval]|alert|json}" ;;
esac
