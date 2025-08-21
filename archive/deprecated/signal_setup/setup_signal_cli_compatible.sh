#!/bin/bash
# Setup Signal CLI with Java 17 compatible version
# Using Signal CLI 0.12.8 which works with Java 17

set -e

echo "🚀 Starting Signal CLI installation (Java 17 compatible)..."

# Define version that works with Java 17
SIGNAL_CLI_VERSION="0.12.8"

# Create directories
mkdir -p ~/signal-cli
cd ~/signal-cli

# Remove old version if exists
if [ -d "signal-cli-0.13.4" ]; then
    echo "🗑️  Removing incompatible version..."
    rm -rf signal-cli-0.13.4
    sudo rm -f /usr/local/bin/signal-cli
fi

# Check if already installed
if [ -f "signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli" ]; then
    echo "✅ Signal CLI ${SIGNAL_CLI_VERSION} already installed"
else
    echo "📥 Downloading Signal CLI v${SIGNAL_CLI_VERSION} (Java 17 compatible)..."
    wget https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz
    
    echo "📦 Extracting Signal CLI..."
    tar xf signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz
    rm signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz
fi

# Create symlink for easy access
echo "🔗 Creating symlink..."
sudo ln -sf ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli /usr/local/bin/signal-cli

# Make script executable
chmod +x ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli

echo ""
echo "📝 Testing Signal CLI..."
signal-cli --version

echo ""
echo "✅ Signal CLI ${SIGNAL_CLI_VERSION} installation complete!"
echo "This version is compatible with Java 17"
echo ""
echo "📱 Next steps:"
echo "1. Register phone number: signal-cli -u +16572463906 register"
echo "2. Verify with SMS code: signal-cli -u +16572463906 verify <CODE>"
echo "3. Create group and get group ID"