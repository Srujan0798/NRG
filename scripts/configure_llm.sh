#!/bin/bash
# LLM Configuration Helper
# Run this to configure LLM API keys

echo "╔══════════════════════════════════════════╗"
echo "║   LLM API Configuration Setup             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Current LLM Configuration:"
echo "  Provider: $(grep LLM_PROVIDER .env | cut -d= -f2)"
echo "  API Key:  $(grep LLM_API_KEY .env | cut -d= -f2 | sed 's/./*/g')"
echo ""

read -p "Enter your LLM provider (gemini/anthropic): " provider
read -p "Enter your API key: " api_key

# Update .env
sed -i '' "s/LLM_PROVIDER=.*/LLM_PROVIDER=$provider/" .env
sed -i '' "s/LLM_API_KEY=.*/LLM_API_KEY=$api_key/" .env

echo ""
echo "✅ Configuration updated!"
echo ""
echo "LLM Integration Notes:"
echo "  - Only schema/metadata sent to LLM (no raw data)"
echo "  - All processing done locally"
echo "  - Responses synthesized from local retrieval"
echo ""
echo "To enable, add to your .env:"
echo "  LLM_PROVIDER=$provider"
echo "  LLM_API_KEY=***"