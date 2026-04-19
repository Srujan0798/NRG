#!/bin/bash
# LLM Setup Helper Script
# Helps users configure their LLM API keys

set -e

echo "🔧 NRG LLM Setup"
echo "================"
echo ""
echo "To enable AI-powered synthesis, you need an API key from one of:"
echo ""
echo "1. Google Gemini (free tier available)"
echo "   https://makersuite.google.com/app/apikey"
echo ""
echo "2. OpenAI GPT-4"
echo "   https://platform.openai.com/api-keys"
echo ""
echo "3. Anthropic Claude"
echo "   https://console.anthropic.com/"
echo ""

read -p "Which provider? (gemini/openai/anthropic): " PROVIDER

if [ -z "$PROVIDER" ]; then
    echo "❌ No provider selected. Exiting."
    exit 1
fi

read -sp "Enter your API key: " API_KEY
echo ""

if [ -z "$API_KEY" ]; then
    echo "❌ No API key entered. Exiting."
    exit 1
fi

# Update .env file
ENV_FILE=".env"

# Backup original
cp "$ENV_FILE" "$ENV_FILE.backup"

# Comment out all LLM keys first
sed -i '' 's/^GEMINI_API_KEY=/# GEMINI_API_KEY=/' "$ENV_FILE"
sed -i '' 's/^OPENAI_API_KEY=/# OPENAI_API_KEY=/' "$ENV_FILE"
sed -i '' 's/^ANTHROPIC_API_KEY=/# ANTHROPIC_API_KEY=/' "$ENV_FILE"

# Set the chosen provider
sed -i '' "s/^LLM_PROVIDER=.*/LLM_PROVIDER=$PROVIDER/" "$ENV_FILE"

# Set the API key
if [ "$PROVIDER" = "gemini" ]; then
    sed -i '' "s/^# GEMINI_API_KEY=.*$/GEMINI_API_KEY=$API_KEY/" "$ENV_FILE"
    echo "✅ Gemini API key configured"
elif [ "$PROVIDER" = "openai" ]; then
    sed -i '' "s/^# OPENAI_API_KEY=.*$/OPENAI_API_KEY=$API_KEY/" "$ENV_FILE"
    echo "✅ OpenAI API key configured"
elif [ "$PROVIDER" = "anthropic" ]; then
    sed -i '' "s/^# ANTHROPIC_API_KEY=.*$/ANTHROPIC_API_KEY=$API_KEY/" "$ENV_FILE"
    echo "✅ Anthropic API key configured"
else
    echo "❌ Unknown provider: $PROVIDER"
    exit 1
fi

echo ""
echo "🎉 LLM configured!"
echo ""
echo "Test with: curl http://localhost:8000/health/llm"
echo "Backup saved to: $ENV_FILE.backup"
