#!/bin/bash

echo "Setting up Briefen.me..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your GEMINI_API_KEY"
else
    echo ".env file already exists"
fi

# Install dependencies
echo "Installing dependencies..."
uv sync

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Run the app with: uv run python main.py"
echo "3. Visit http://localhost:5000"
echo ""