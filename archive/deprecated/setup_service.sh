#!/bin/bash
# Setup script for Daily Financial Alerts and Signal API services

echo "🚀 Setting up Daily Financial Alerts automation services..."

# Ensure user is in docker group
if ! groups $USER | grep -q '\bdocker\b'; then
    echo "👤 Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo "⚠️ Please log out and log back in for docker group changes to take effect"
fi

# Copy service files to systemd
echo "📁 Installing service files..."
sudo cp signal-api.service /etc/systemd/system/
sudo cp daily-alerts.service /etc/systemd/system/
sudo cp daily-alerts-failure.service /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services to start on boot
echo "🔧 Enabling services for auto-start..."
sudo systemctl enable signal-api.service
sudo systemctl enable daily-alerts.service

# Start Signal API service first
echo "📡 Starting Signal API service..."
sudo systemctl start signal-api.service

# Wait for Signal API to be ready
echo "⏳ Waiting for Signal API to be ready..."
sleep 10

# Check if Signal API is running
if systemctl is-active --quiet signal-api.service; then
    echo "✅ Signal API service is running"
else
    echo "❌ Signal API service failed to start"
    sudo journalctl -u signal-api.service --no-pager -n 20
fi

# Start daily alerts service
echo "📊 Starting Daily Alerts service..."
sudo systemctl start daily-alerts.service

# Check service status
sleep 5
if systemctl is-active --quiet daily-alerts.service; then
    echo "✅ Daily Alerts service is running"
else
    echo "❌ Daily Alerts service failed to start"
    sudo journalctl -u daily-alerts.service --no-pager -n 20
fi

echo ""
echo "✅ Service setup complete!"
echo ""
echo "📊 Service commands:"
echo "  Signal API status: sudo systemctl status signal-api"
echo "  Alerts status:     sudo systemctl status daily-alerts"
echo "  Start both:        sudo systemctl start signal-api daily-alerts"
echo "  Stop both:         sudo systemctl stop daily-alerts signal-api"
echo "  View logs:         sudo journalctl -u daily-alerts -f"
echo "  Signal API logs:   sudo journalctl -u signal-api -f"
echo ""
echo "⏰ Scheduled for 8:00 AM PST on weekdays"
echo "🔧 Services will auto-restart on failure and boot"
echo "📱 Both Signal and Telegram messaging enabled"
echo ""
echo "💡 Test the system manually:"
echo "  source venv/bin/activate && python run_full_automation.py"