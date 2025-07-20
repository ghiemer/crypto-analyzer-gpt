#!/bin/bash

# =============================================================================
# RENDER LIVE LOG MONITORING SCRIPT
# =============================================================================
# This script provides real-time logging from your Render deployment
# Usage: ./monitor_render_logs.sh [service-name] [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SERVICE_NAME=${1:-"crypto-analyzer-gpt"}
ENVIRONMENT=${2:-"production"}

echo -e "${CYAN}🚀 RENDER LIVE LOG MONITOR${NC}"
echo -e "${CYAN}===============================${NC}"
echo -e "${YELLOW}Service:${NC} $SERVICE_NAME"
echo -e "${YELLOW}Environment:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Timestamp:${NC} $(date)"
echo ""

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${RED}❌ Render CLI not found!${NC}"
    echo -e "${YELLOW}Install with: ${NC}brew install render"
    exit 1
fi

# Check if user is logged in
if ! render whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged into Render CLI${NC}"
    echo -e "${YELLOW}Login with: ${NC}render auth login"
    exit 1
fi

echo -e "${GREEN}✅ Render CLI ready${NC}"
echo -e "${BLUE}📊 Starting live log stream...${NC}"
echo ""

# Function to handle Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}🛑 Log monitoring stopped${NC}"
    exit 0
}
trap cleanup SIGINT

# Start live log streaming
echo -e "${PURPLE}📋 LIVE LOGS (Press Ctrl+C to stop):${NC}"
echo -e "${CYAN}===========================================${NC}"

render logs --service="$SERVICE_NAME" --tail

# If render logs fails, try alternative approach
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Direct log access failed, trying service list...${NC}"
    echo ""
    echo -e "${CYAN}Available services:${NC}"
    render services list
    echo ""
    echo -e "${YELLOW}💡 Usage: ./monitor_render_logs.sh <exact-service-name>${NC}"
fi
