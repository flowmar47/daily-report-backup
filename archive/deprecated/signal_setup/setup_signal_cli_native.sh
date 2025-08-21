#!/bin/bash
# Setup Signal CLI Native version (no Java required!)
# Using the native Linux build that doesn't need Java

set -e

echo "🚀 Starting Signal CLI Native installation (no Java required!)..."

# Define native version
SIGNAL_CLI_VERSION="0.13.15"

# Create directories
mkdir -p ~/signal-cli
cd ~/signal-cli

# Remove old versions if exist
if [ -d "signal-cli-0.13.4" ] || [ -d "signal-cli-0.12.8" ]; then
    echo "🗑️  Removing old versions..."
    rm -rf signal-cli-*
    sudo rm -f /usr/local/bin/signal-cli
fi

# Check if already installed
if [ -f "signal-cli-${SIGNAL_CLI_VERSION}-Linux-native/bin/signal-cli" ]; then
    echo "✅ Signal CLI Native ${SIGNAL_CLI_VERSION} already installed"
else
    echo "📥 Downloading Signal CLI Native v${SIGNAL_CLI_VERSION}..."
    wget https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-Linux-native.tar.gz
    
    echo "📦 Extracting Signal CLI Native..."
    tar xf signal-cli-${SIGNAL_CLI_VERSION}-Linux-native.tar.gz
    rm signal-cli-${SIGNAL_CLI_VERSION}-Linux-native.tar.gz
fi

# Create symlink for easy access
echo "🔗 Creating symlink..."
sudo ln -sf ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}-Linux-native/bin/signal-cli /usr/local/bin/signal-cli

# Make executable
chmod +x ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}-Linux-native/bin/signal-cli

# Install any native dependencies
echo "📦 Installing native dependencies..."
sudo apt-get update
sudo apt-get install -y libsqlite3-0 libssl3

echo ""
echo "📝 Testing Signal CLI Native..."
signal-cli --version || echo "Testing..."

echo ""
echo "✅ Signal CLI Native ${SIGNAL_CLI_VERSION} installation complete!"
echo "🎉 No Java required - using native Linux build!"
echo ""
echo "📱 Next steps:"
echo "1. Register phone number: signal-cli -u +16572463906 register"
echo "2. Verify with SMS code: signal-cli -u +16572463906 verify <CODE>"
echo "3. Create group and get group ID"