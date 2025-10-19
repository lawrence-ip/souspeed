#!/bin/bash

echo "🚀 SousSpeed Digital Ocean Deployment Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as a regular user, not root"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update

# Install required system packages
print_status "Installing system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv nginx curl docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
print_warning "You may need to log out and back in for docker permissions to take effect"

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test the application
print_status "Testing application..."
python3 -c "from app import app; print('✅ Flask app imports successfully')"
python3 -c "from thermo_calculator import ThermodynamicCalculator; print('✅ Calculator imports successfully')"

# Option 1: Docker deployment (recommended)
echo ""
echo "Choose deployment method:"
echo "1) Docker with port 8080 (DigitalOcean App Platform)"
echo "2) Docker with port 80 (Traditional droplet)"
echo "3) Direct Python with nginx"
echo "4) Simple Python server (development only)"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        print_status "Deploying with Docker (DigitalOcean App Platform - port 8080)..."
        
        # Create app platform docker-compose
        cat > docker-compose.app.yml << EOF
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - PORT=8080
    restart: unless-stopped
EOF
        
        # Build and start
        sudo docker-compose -f docker-compose.app.yml down 2>/dev/null || true
        sudo docker-compose -f docker-compose.app.yml build
        sudo docker-compose -f docker-compose.app.yml up -d
        
        # Wait and test
        sleep 15
        if curl -s http://localhost:8080/api/health > /dev/null; then
            print_status "Docker deployment successful on port 8080!"
            print_status "Application ready for DigitalOcean App Platform"
        else
            print_error "Docker deployment failed"
            sudo docker-compose -f docker-compose.app.yml logs
        fi
        ;;
        
    2)
        print_status "Deploying with Docker (Traditional - port 80)..."
        
        # Use original docker-compose with port 80
        sed -i 's/8080/5000/g' docker-compose.yml
        sed -i 's/"80:8080"/"80:5000"/g' docker-compose.yml
        
        sudo docker-compose down 2>/dev/null || true
        sudo docker-compose build
        sudo docker-compose up -d
        
        sleep 10
        if curl -s http://localhost/api/health > /dev/null; then
            print_status "Docker deployment successful!"
            print_status "Application is running at: http://$(curl -s ifconfig.me)"
        else
            print_error "Docker deployment failed"
            sudo docker-compose logs
        fi
        ;;
        
    3)
        print_status "Deploying with nginx reverse proxy..."
        
        # Create nginx configuration
        sudo tee /etc/nginx/sites-available/souspeed << EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

        # Enable the site
        sudo ln -sf /etc/nginx/sites-available/souspeed /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        sudo nginx -t && sudo systemctl reload nginx

        # Create systemd service
        sudo tee /etc/systemd/system/souspeed.service << EOF
[Unit]
Description=SousSpeed Flask Application
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
Environment=FLASK_ENV=production
ExecStart=$PWD/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 60 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

        # Start and enable the service
        sudo systemctl daemon-reload
        sudo systemctl enable souspeed
        sudo systemctl start souspeed
        
        # Test the deployment
        sleep 5
        if curl -s http://localhost/api/health > /dev/null; then
            print_status "Nginx deployment successful!"
            print_status "Application is running at: http://$(curl -s ifconfig.me)"
        else
            print_error "Deployment failed"
            sudo systemctl status souspeed
        fi
        ;;
        
    4)
        print_status "Starting development server..."
        print_warning "This is not recommended for production!"
        
        export FLASK_ENV=production
        python3 app.py &
        APP_PID=$!
        
        sleep 3
        if curl -s http://localhost:5000/api/health > /dev/null; then
            print_status "Development server started!"
            print_status "Application is running at: http://$(curl -s ifconfig.me):5000"
            print_warning "Press Ctrl+C to stop"
            wait $APP_PID
        else
            print_error "Failed to start development server"
        fi
        ;;
        
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_status "Deployment complete!"
echo "📋 Useful commands:"
echo "   Check status: sudo systemctl status souspeed"
echo "   View logs: sudo journalctl -u souspeed -f"
echo "   Restart: sudo systemctl restart souspeed"
echo "   Docker logs: sudo docker-compose logs -f"
