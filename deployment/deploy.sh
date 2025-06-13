#!/bin/bash

# Bot Slack Service Deployment Script
# This script automates the deployment process for the Bot Slack service

set -e  # Exit on any error

# Configuration
APP_NAME="bot-slack"
APP_DIR="/opt/${APP_NAME}"
SERVICE_USER="www-data"
PYTHON_VERSION="3.9"
REPO_URL="https://github.com/your-org/bot-slack.git"  # Update with your repo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        git \
        nginx \
        supervisor \
        curl \
        wget \
        unzip
    
    log_success "System dependencies installed"
}

# Create application user
create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        log "Creating service user: $SERVICE_USER"
        useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $SERVICE_USER
        log_success "Service user created"
    else
        log "Service user $SERVICE_USER already exists"
    fi
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    # Create directories
    mkdir -p $APP_DIR
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/reports
    
    # Set ownership
    chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR
    
    log_success "Application directory setup complete"
}

# Clone or update repository
setup_repository() {
    log "Setting up repository..."
    
    if [ -d "$APP_DIR/.git" ]; then
        log "Updating existing repository..."
        cd $APP_DIR
        sudo -u $SERVICE_USER git pull origin main
    else
        log "Cloning repository..."
        sudo -u $SERVICE_USER git clone $REPO_URL $APP_DIR
    fi
    
    log_success "Repository setup complete"
}

# Setup Python virtual environment
setup_virtualenv() {
    log "Setting up Python virtual environment..."
    
    cd $APP_DIR
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        sudo -u $SERVICE_USER python${PYTHON_VERSION} -m venv venv
    fi
    
    # Activate and upgrade pip
    sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
    
    # Install requirements
    sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"
    
    log_success "Virtual environment setup complete"
}

# Setup environment file
setup_environment() {
    log "Setting up environment configuration..."
    
    if [ ! -f "$APP_DIR/.env" ]; then
        log_warning "Creating .env file template"
        cat > $APP_DIR/.env << EOF
# Slack Configuration
TOKEN_SLACK=xoxb-your-slack-bot-token
GROUP_ID_SLACK=your-slack-channel-id

# Report Configuration
DEFAULT_URL_REPORT=http://your-report-server.com
REPORT_PATH_MLM=/path/to/mlm/reports
REPORT_PATH_ADMIN=/path/to/admin/reports
REPORT_PATH_DOB=/path/to/dob/reports
REPORT_PATH_VKYC=/path/to/vkyc/reports

# Batch File Paths
BATCH_MLM=/path/to/mlm.bat
BATCH_ADMIN=/path/to/admin.bat
BATCH_DOB=/path/to/dob.bat
BATCH_VKYC=/path/to/vkyc.bat

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        chown $SERVICE_USER:$SERVICE_USER $APP_DIR/.env
        chmod 600 $APP_DIR/.env
        
        log_warning "Please edit $APP_DIR/.env with your actual configuration"
    else
        log "Environment file already exists"
    fi
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Copy service file
    cp $APP_DIR/bot-slack.service /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable bot-slack
    
    log_success "Systemd service setup complete"
}

# Setup nginx
setup_nginx() {
    log "Setting up nginx configuration..."
    
    # Copy nginx configuration
    cp $APP_DIR/nginx.conf /etc/nginx/sites-available/bot-slack
    
    # Enable site
    ln -sf /etc/nginx/sites-available/bot-slack /etc/nginx/sites-enabled/
    
    # Remove default site if it exists
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx setup complete"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start bot service
    systemctl start bot-slack
    
    # Check status
    if systemctl is-active --quiet bot-slack; then
        log_success "Bot Slack service started successfully"
    else
        log_error "Failed to start Bot Slack service"
        systemctl status bot-slack
        exit 1
    fi
    
    # Check nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx started successfully"
    else
        log_error "Failed to start Nginx"
        systemctl status nginx
        exit 1
    fi
}

# Setup firewall (optional)
setup_firewall() {
    log "Setting up firewall rules..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp   # SSH
        ufw allow 80/tcp   # HTTP
        ufw allow 443/tcp  # HTTPS
        ufw --force enable
        log_success "Firewall configured"
    else
        log_warning "UFW not installed, skipping firewall setup"
    fi
}

# Main deployment function
deploy() {
    log "Starting Bot Slack Service deployment..."
    
    check_root
    install_dependencies
    create_user
    setup_app_directory
    setup_repository
    setup_virtualenv
    setup_environment
    setup_systemd
    setup_nginx
    setup_firewall
    start_services
    
    log_success "Deployment completed successfully!"
    log "Service status:"
    systemctl status bot-slack --no-pager
    
    log "\nUseful commands:"
    log "  - Check service status: systemctl status bot-slack"
    log "  - View logs: journalctl -u bot-slack -f"
    log "  - Restart service: systemctl restart bot-slack"
    log "  - Check health: curl http://localhost/health"
}

# Update function for existing deployments
update() {
    log "Updating Bot Slack Service..."
    
    # Stop service
    systemctl stop bot-slack
    
    # Update code
    setup_repository
    setup_virtualenv
    
    # Start service
    systemctl start bot-slack
    
    log_success "Update completed successfully!"
}

# Uninstall function
uninstall() {
    log "Uninstalling Bot Slack Service..."
    
    # Stop and disable services
    systemctl stop bot-slack || true
    systemctl disable bot-slack || true
    
    # Remove service file
    rm -f /etc/systemd/system/bot-slack.service
    systemctl daemon-reload
    
    # Remove nginx configuration
    rm -f /etc/nginx/sites-enabled/bot-slack
    rm -f /etc/nginx/sites-available/bot-slack
    systemctl restart nginx
    
    # Remove application directory
    read -p "Remove application directory $APP_DIR? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf $APP_DIR
        log_success "Application directory removed"
    fi
    
    log_success "Uninstallation completed"
}

# Show usage
usage() {
    echo "Usage: $0 {deploy|update|uninstall}"
    echo "  deploy    - Full deployment (first time setup)"
    echo "  update    - Update existing deployment"
    echo "  uninstall - Remove the service"
    exit 1
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    uninstall)
        uninstall
        ;;
    *)
        usage
        ;;
esac