#!/bin/bash
# Script to update Nginx configuration for WebSocket support

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Updating Nginx configuration for WebSocket support ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Please run as root or with sudo${NC}"
  exit 1
fi

# Backup the current configuration
NGINX_CONF="/etc/nginx/sites-available/product-review-analyzer"
BACKUP_FILE="${NGINX_CONF}.bak.$(date +%Y%m%d%H%M%S)"

if [ -f "$NGINX_CONF" ]; then
  echo "Creating backup of current Nginx configuration: $BACKUP_FILE"
  cp "$NGINX_CONF" "$BACKUP_FILE"
else
  echo -e "${RED}Nginx configuration file not found at $NGINX_CONF${NC}"
  echo "Creating a new configuration file"
fi

# Create updated Nginx configuration
echo "Creating updated Nginx configuration with WebSocket support"
cat > "$NGINX_CONF" << EOL
server {
    listen 80;
    server_name _;  # Will match any hostname

    # Serve frontend static files directly
    location / {
        root $(pwd)/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to the backend
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Serve API documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Serve OpenAPI schema
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support for /ws endpoint
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support for /public-ws endpoint
    location /public-ws {
        proxy_pass http://localhost:8000/public-ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support for /ws-public endpoint
    location /ws-public {
        proxy_pass http://localhost:8000/ws-public;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Test Nginx configuration
echo "Testing Nginx configuration"
nginx -t

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Nginx configuration is valid${NC}"
  echo "Restarting Nginx"
  systemctl restart nginx
  echo -e "${GREEN}Nginx has been restarted with the updated configuration${NC}"
else
  echo -e "${RED}Nginx configuration is invalid. Please check the configuration.${NC}"
  echo "Restoring backup configuration"
  cp "$BACKUP_FILE" "$NGINX_CONF"
  systemctl restart nginx
  exit 1
fi

echo -e "${GREEN}WebSocket configuration update completed successfully${NC}"
