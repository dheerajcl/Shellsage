#!/bin/bash

# Shell Sage Installation Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Shell Sage Installation...${NC}"

# # Check for Python 3.8+
# if ! python3 -c 'import sys; exit(1) if sys.version_info < (3,8) else exit(0)' &>/dev/null; then
#     echo -e "${RED}❌ Python 3.8 or newer is required${NC}"
#     exit 1
# fi

# Create virtual environment
if [ ! -d "shellsage_env" ]; then
    echo -e "${YELLOW}⚙️ Creating virtual environment...${NC}"
    python3 -m venv shellsage_env
else
    echo -e "${YELLOW}⚙️ Using existing virtual environment...${NC}"
fi

# Activate virtual environment
source shellsage_env/bin/activate

# Install system dependencies
echo -e "${YELLOW}⚙️ Checking for system dependencies...${NC}"
if ! command -v ollama &>/dev/null; then
    echo -e "${YELLOW}⚠️ Ollama not found. Install from https://ollama.ai/ for local models${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}⚙️ Installing Python dependencies...${NC}"
pip install -U pip
pip install -r requirements.txt

# Install in editable mode
echo -e "${YELLOW}⚙️ Installing Shell Sage...${NC}"
pip install -e .

# Post-install setup
echo -e "${YELLOW}⚙️ Running initial configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ Creating .env file from example...${NC}"
    cp .env.example .env
fi
shellsage setup

# Install shell hook
echo -e "${YELLOW}⚙️ Installing shell hook...${NC}"
HOOK=$(shellsage install | sed -n '/^# Add this to your shell config:/,/^$/p' | sed '1d;$d')

if [ -f ~/.bashrc ]; then
    echo "$HOOK" >> ~/.bashrc
    echo -e "${GREEN}✅ Added to ~/.bashrc${NC}"
fi

if [ -f ~/.zshrc ]; then
    echo "$HOOK" >> ~/.zshrc
    echo -e "${GREEN}✅ Added to ~/.zshrc${NC}"
fi

echo -e "\n${GREEN}✅ Installation Complete!${NC}"
echo -e "To start using Shell Sage:"
echo -e "1. Activate environment: ${YELLOW}source shellsage_env/bin/activate${NC}"
echo -e "2. Add api keys and your desired model supported by the listed providers manually in .env if the model you intend to use is not listed${NC}"
echo -e "3. Test installation: ${YELLOW}shellsage ask 'update packages'${NC}"
echo -e "4. For local models: ${YELLOW}ollama pull llama3:8b-instruct-q4_1${NC}"

exit 0