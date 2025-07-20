#!/bin/bash
# Render Log Monitor - Simple bash version
# Automatically loads service ID from .env and starts log monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to load .env file
load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
        echo -e "${GREEN}✅ Loaded configuration from .env${NC}"
    else
        echo -e "${RED}❌ .env file not found${NC}"
        exit 1
    fi
}

# Function to check if render CLI is available
check_render_cli() {
    if ! command -v render &> /dev/null; then
        echo -e "${RED}❌ Render CLI not found${NC}"
        echo "📦 Install with: npm install -g @render/cli"
        echo "🔑 Login with: render auth login"
        exit 1
    fi
}

# Main function
main() {
    echo -e "${BLUE}🔧 Render Log Monitor${NC}"
    echo "================================="
    
    # Load environment variables
    load_env
    
    # Check dependencies
    check_render_cli
    
    # Check if service ID is set
    if [ -z "$RENDER_SERVICE_ID" ]; then
        echo -e "${RED}❌ RENDER_SERVICE_ID not found in .env${NC}"
        echo "📝 Please add RENDER_SERVICE_ID=your-service-id to .env"
        exit 1
    fi
    
    SERVICE_NAME=${RENDER_SERVICE_NAME:-"crypto-analyzer-gpt"}
    
    echo -e "${GREEN}🚀 Starting log monitoring${NC}"
    echo -e "${YELLOW}📊 Service: $SERVICE_NAME${NC}"
    echo -e "${YELLOW}🆔 ID: $RENDER_SERVICE_ID${NC}"
    echo -e "${YELLOW}⏰ Started: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo "================================="
    echo -e "${BLUE}💡 Press Ctrl+C to stop${NC}"
    echo ""
    
    # Start render logs with tail mode (non-interactive)
    exec render logs "$RENDER_SERVICE_ID" --tail
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}🛑 Monitoring stopped${NC}"; exit 0' INT

# Run main function
main
