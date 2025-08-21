#!/bin/bash
# Setup persistent Signal CLI with proper restart policies

set -e

echo "🔧 Setting up persistent Signal CLI with auto-restart..."

# Stop and remove existing container
echo "🛑 Stopping existing container..."
sudo docker stop signal-api 2>/dev/null || true
sudo docker rm signal-api 2>/dev/null || true

# Create persistent volume for Signal data
echo "📁 Creating Docker volume for persistent data..."
sudo docker volume create signal-data

# Create systemd service for Signal API
echo "🚀 Creating systemd service for auto-start..."
sudo tee /etc/systemd/system/signal-api.service > /dev/null << 'EOF'
[Unit]
Description=Signal CLI REST API Docker Container
Requires=docker.service
After=docker.service
StartLimitBurst=3
StartLimitInterval=60s

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
ExecStartPre=-/usr/bin/docker stop signal-api
ExecStartPre=-/usr/bin/docker rm signal-api
ExecStart=/usr/bin/docker run --rm \
    --name signal-api \
    -p 8080:8080 \
    -v signal-data:/home/.local/share/signal-cli \
    -v /etc/localtime:/etc/localtime:ro \
    bbernhard/signal-cli-rest-api:latest
ExecStop=/usr/bin/docker stop signal-api

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "⚙️ Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable signal-api.service
sudo systemctl start signal-api.service

# Wait for service to start
echo "⏳ Waiting for Signal API to start..."
sleep 15

# Check service status
if sudo systemctl is-active --quiet signal-api.service; then
    echo "✅ Signal API service is running!"
else
    echo "❌ Service failed to start. Checking logs..."
    sudo journalctl -u signal-api.service -n 20
    exit 1
fi

# Check API
if curl -s http://localhost:8080/v1/about > /dev/null; then
    echo "✅ Signal API is responding!"
else
    echo "⚠️ API not responding yet, waiting more..."
    sleep 10
fi

# Create backup script
echo "💾 Creating backup script..."
cat > ~/signal-backup.sh << 'BACKUP_EOF'
#!/bin/bash
# Backup Signal data
BACKUP_DIR=~/signal-backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
sudo docker run --rm -v signal-data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/signal-backup-$DATE.tar.gz -C /data .
echo "Backup saved to $BACKUP_DIR/signal-backup-$DATE.tar.gz"
# Keep only last 7 backups
cd $BACKUP_DIR && ls -t signal-backup-*.tar.gz | tail -n +8 | xargs -r rm
BACKUP_EOF
chmod +x ~/signal-backup.sh

# Add cron job for daily backups
echo "⏰ Setting up daily backups..."
(crontab -l 2>/dev/null; echo "0 3 * * * /home/ohms/signal-backup.sh") | crontab -

echo ""
echo "✅ Persistent Signal setup complete!"
echo ""
echo "📋 Summary:"
echo "   - Docker volume: signal-data (persistent storage)"
echo "   - Systemd service: signal-api.service (auto-restart)"
echo "   - Auto-start: Enabled on system boot"
echo "   - Daily backups: 3 AM to ~/signal-backups"
echo ""
echo "🔧 Service commands:"
echo "   sudo systemctl status signal-api    # Check status"
echo "   sudo systemctl restart signal-api   # Restart"
echo "   sudo journalctl -u signal-api -f    # View logs"
echo ""
echo "📱 Next: Run registration with CAPTCHA"
echo "   python register_signal_captcha.py"