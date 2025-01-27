#!/bin/bash

# Shell Sage Installation Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting Shell Sage Installation...${NC}"

# Create virtual environment
if [ ! -d "shellsage_env" ]; then
    echo -e "${YELLOW}⚙️ Creating virtual environment...${NC}"
    python3 -m venv shellsage_env
else
    echo -e "${YELLOW}⚙️ Using existing virtual environment...${NC}"
fi

# Activate virtual environment
source shellsage_env/bin/activate

# After activating venv, before installing dependencies
echo -e "${YELLOW}🔑 API Key Setup (Required for LLM features)...${NC}"

# Check if key already exists
if [ -z "$GROQ_API_KEY" ]; then
    read -p "Enter your Groq API key (get it from https://groq.com/#): " api_key
    echo "export GROQ_API_KEY='$api_key'" >> shellsage_env/bin/activate
    echo "export GROQ_API_KEY='$api_key'" >> ~/.bashrc
fi

# Reload activation script
source shellsage_env/bin/activate

# Install dependencies
echo -e "${YELLOW}⚙️ Installing dependencies...${NC}"
pip3 install requests click openai

# Install in editable mode
echo -e "${YELLOW}⚙️ Installing Shell Sage...${NC}"
pip3 install -e .

# Post-install setup
echo -e "${YELLOW}⚙️ Configuring shell integration...${NC}"
shellsage install >> ~/.bashrc || true

echo -e "\n${GREEN}✅ Installation Complete!${NC}"
echo -e "To start using Shell Sage:"
echo -e "1. Update current shell: ${YELLOW}source ~/.bashrc${NC}"
echo -e "2. Activate virtual environment: ${YELLOW}source shellsage_env/bin/activate${NC}"
echo -e "3. Test installation: ${YELLOW}shellsage ask 'update packages'${NC}"

echo -e "${YELLOW}ℹ️ To set API key later:"
echo -e "1. Edit ~/.bashrc and add:"
echo -e "   export GROQ_API_KEY='your_api_key'"
echo -e "2. Run: source ~/.bashrc${NC}"

exit 0