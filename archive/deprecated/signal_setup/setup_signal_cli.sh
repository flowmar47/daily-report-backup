#!/bin/bash
# Setup Signal CLI on Raspberry Pi
# Based on https://github.com/pmatuszy/signal-cli-on-Raspberry-PI---WORKS-

set -e

echo "🚀 Starting Signal CLI installation..."

# Define version
SIGNAL_CLI_VERSION="0.13.4"

# Create directories
mkdir -p ~/signal-cli
cd ~/signal-cli

# Check if already installed
if [ -f "signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli" ]; then
    echo "✅ Signal CLI ${SIGNAL_CLI_VERSION} already installed"
else
    echo "📥 Downloading Signal CLI v${SIGNAL_CLI_VERSION}..."
    wget https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}.tar.gz
    
    echo "📦 Extracting Signal CLI..."
    tar xf signal-cli-${SIGNAL_CLI_VERSION}.tar.gz
    rm signal-cli-${SIGNAL_CLI_VERSION}.tar.gz
fi

# Create symlink for easy access
echo "🔗 Creating symlink..."
sudo ln -sf ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli /usr/local/bin/signal-cli

# Check Java installation
echo "☕ Checking Java installation..."
if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Installing OpenJDK..."
    sudo apt-get update
    sudo apt-get install -y openjdk-17-jre-headless
else
    echo "✅ Java is installed"
    java -version
fi

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get install -y libunixsocket-java

# Create config directory
mkdir -p ~/.local/share/signal-cli

echo "✅ Signal CLI installation complete!"
echo "📱 Next steps:"
echo "1. Register phone number: signal-cli -u +16572463906 register"
echo "2. Verify with SMS code: signal-cli -u +16572463906 verify <CODE>"
echo "3. Create group and get group ID"

# Make script executable
chmod +x ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli

echo ""
echo "📝 Testing Signal CLI..."
signal-cli --version || echo "⚠️ Signal CLI test failed"