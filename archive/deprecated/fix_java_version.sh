#!/bin/bash
# Fix Java version for Signal CLI
# Signal CLI 0.13.4 requires Java 21

set -e

echo "🔧 Fixing Java version for Signal CLI..."
echo "Signal CLI 0.13.4 requires Java 21, but Java 17 is installed"

# Check current Java version
echo ""
echo "📋 Current Java version:"
java -version

# Install Java 21
echo ""
echo "📥 Installing OpenJDK 21..."
sudo apt-get update
sudo apt-get install -y openjdk-21-jre-headless

# Update alternatives to use Java 21
echo ""
echo "🔄 Setting Java 21 as default..."
sudo update-alternatives --set java /usr/lib/jvm/java-21-openjdk-arm64/bin/java

# Verify new version
echo ""
echo "✅ New Java version:"
java -version

# Test Signal CLI
echo ""
echo "🧪 Testing Signal CLI with new Java version..."
signal-cli --version || echo "⚠️ Signal CLI test failed"

echo ""
echo "✅ Java version fixed! You can now run the registration script."