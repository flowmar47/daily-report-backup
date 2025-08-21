#!/bin/bash
# Setup Signal CLI for ARM64 (Raspberry Pi)
# Using older version compatible with Java 17

set -e

echo "🚀 Starting Signal CLI installation for ARM64 (Raspberry Pi)..."

# Define version compatible with Java 17
SIGNAL_CLI_VERSION="0.11.11"

# Create directories
mkdir -p ~/signal-cli
cd ~/signal-cli

# Clean up previous attempts
echo "🗑️  Cleaning up previous installations..."
rm -rf signal-cli-* signal-cli
sudo rm -f /usr/local/bin/signal-cli

# Download Signal CLI
echo "📥 Downloading Signal CLI v${SIGNAL_CLI_VERSION} (Java 17 compatible)..."
wget https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz

echo "📦 Extracting Signal CLI..."
tar xf signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz
rm signal-cli-${SIGNAL_CLI_VERSION}-Linux.tar.gz

# Create symlink for easy access
echo "🔗 Creating symlink..."
sudo ln -sf ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli /usr/local/bin/signal-cli

# Make script executable
chmod +x ~/signal-cli/signal-cli-${SIGNAL_CLI_VERSION}/bin/signal-cli

# Test Java version
echo ""
echo "☕ Current Java version:"
java -version

echo ""
echo "📝 Testing Signal CLI..."
signal-cli --version || echo "Note: Some warnings are normal on first run"

echo ""
echo "✅ Signal CLI ${SIGNAL_CLI_VERSION} installation complete!"
echo "This version is compatible with Java 17 on ARM64"
echo ""
echo "📱 Next steps:"
echo "1. Register phone number: signal-cli -u +16572463906 register"
echo "2. Verify with SMS code: signal-cli -u +16572463906 verify <CODE>"
echo "3. Create group and get group ID"