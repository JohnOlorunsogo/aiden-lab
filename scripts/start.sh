#!/bin/bash

# AIDEN Labs - Unified Startup Script (Linux/macOS)

# This script starts both the backend and frontend services.
# Usage: ./start.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script's directory (project root is parent of scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# PID tracking for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Set up trap for cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Print banner
echo -e "${BLUE}"
echo "        AIDEN Labs - Starting Services       "
echo -e "${NC}"

# Check if directories exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Start Backend
echo -e "${GREEN}Starting Backend...${NC}"
cd "$BACKEND_DIR"

# Check for virtual environment and activate if exists
if [ -f "$PROJECT_ROOT/bin/activate" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/bin/activate"
elif [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Checking Python dependencies...${NC}"
    pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
fi

python run.py &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Give backend a moment to start
sleep 2

# Start Frontend
echo -e "${GREEN}Starting Frontend...${NC}"
cd "$FRONTEND_DIR"

# Check if bun is installed
if ! command -v bun &> /dev/null; then
    echo -e "${RED}Error: bun is not installed. Please install bun to run the frontend.${NC}"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    bun install
fi

echo -e "${BLUE}Building frontend for production...${NC}"
bun run build

echo -e "${BLUE}Starting frontend preview server...${NC}"
bun run preview &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

# Print status

echo -e "${GREEN}Services are running:${NC}"
echo -e "  ${BLUE}Backend:${NC}  http://localhost:8000"
echo -e "  ${BLUE}Frontend:${NC} http://localhost:4173"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
