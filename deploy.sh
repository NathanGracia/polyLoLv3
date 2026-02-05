#!/bin/bash
# 🚀 Deployment script for PolyBet

set -e  # Exit on error

echo "🚀 Deploying PolyBet..."

# 1. Pull latest code
echo "📥 Pulling latest changes..."
git pull

# 2. Stop current containers
echo "🛑 Stopping containers..."
sudo docker-compose down

# 3. Rebuild containers
echo "🔨 Building containers..."
sudo docker-compose build --no-cache

# 4. Start containers
echo "▶️  Starting containers..."
sudo docker-compose up -d

# 5. Update nginx config if changed
if [ -f "nginx.conf" ]; then
    echo "🔧 Updating nginx config..."
    sudo cp nginx.conf /etc/nginx/sites-available/polybet
    sudo nginx -t && sudo systemctl reload nginx
fi

# 6. Show logs
echo "📋 Container logs:"
sudo docker-compose logs --tail=20

echo ""
echo "✅ Deployment complete!"
echo "🌐 Check: https://polybet.nathangracia.com"
