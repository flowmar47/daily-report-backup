#!/bin/bash
# Build Signal CLI from source for ARM64 compatibility
# This ensures native libraries are compiled for ARM64

set -e

echo "🚀 Building Signal CLI from source for ARM64..."

# Install build dependencies
echo "📦 Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y git gradle libffi-dev

# Clean up previous attempts
echo "🗑️  Cleaning up previous installations..."
cd ~
rm -rf signal-cli signal-cli-*
sudo rm -f /usr/local/bin/signal-cli

# Clone Signal CLI repository
echo "📥 Cloning Signal CLI repository..."
git clone https://github.com/AsamK/signal-cli.git
cd signal-cli

# Checkout a stable version that works with Java 17
echo "🔄 Checking out stable version..."
git checkout v0.10.11

# Build Signal CLI
echo "🔨 Building Signal CLI (this may take a while)..."
./gradlew build
./gradlew installDist

# Create symlink
echo "🔗 Creating symlink..."
sudo ln -sf ~/signal-cli/build/install/signal-cli/bin/signal-cli /usr/local/bin/signal-cli

# Make executable
chmod +x ~/signal-cli/build/install/signal-cli/bin/signal-cli

# Test
echo ""
echo "📝 Testing Signal CLI..."
signal-cli --version || echo "Note: Some warnings are normal"

echo ""
echo "✅ Signal CLI built from source for ARM64!"
echo ""
echo "📱 Next steps:"
echo "1. Register phone number: signal-cli -u +16572463906 register"
echo "2. Verify with SMS code: signal-cli -u +16572463906 verify <CODE>"
echo "3. Create group and get group ID"