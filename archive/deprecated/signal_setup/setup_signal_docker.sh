#!/bin/bash
# Setup Signal using Docker (signal-cli-rest-api)
# This is much easier and works on ARM64

set -e

echo "🚀 Setting up Signal using Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in for Docker permissions to take effect"
fi

# Create directory for Signal data
echo "📁 Creating Signal data directory..."
mkdir -p ~/signal-api-data

# Pull the signal-cli-rest-api image (ARM64 compatible)
echo "📥 Pulling Signal API Docker image..."
docker pull bbernhard/signal-cli-rest-api:latest

# Run the container
echo "🚀 Starting Signal API container..."
docker run -d \
    --name signal-api \
    --restart unless-stopped \
    -p 8080:8080 \
    -v ~/signal-api-data:/home/.local/share/signal-cli \
    -e MODE=native \
    bbernhard/signal-cli-rest-api:latest

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check if running
if docker ps | grep -q signal-api; then
    echo "✅ Signal API container is running!"
    echo ""
    echo "📱 Next steps:"
    echo "1. Register phone number using the web API"
    echo "2. Create group and get group ID"
    echo "3. Send messages via REST API"
    echo ""
    echo "🌐 Signal API is available at: http://localhost:8080"
    echo "📚 API docs: http://localhost:8080/v1/api-docs"
else
    echo "❌ Failed to start Signal API container"
    docker logs signal-api
fi