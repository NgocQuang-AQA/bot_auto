#!/bin/bash

# Bot Slack Deployment Script
# Enhanced version with CI/CD support
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh production deploy
#          ./deploy.sh staging rollback

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ===========================================
# CONFIGURATION
# ===========================================

# Default values
ENVIRONMENT=${1:-staging}
ACTION=${2:-deploy}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/bot-slack-deploy.log"
BACKUP_DIR="/opt/backups/bot-slack"
MAX_BACKUPS=5

# Environment-specific configurations
case $ENVIRONMENT in
    "production")
        COMPOSE_FILE="docker-compose.yml"
        IMAGE_TAG="latest"
        HEALTH_CHECK_URL="http://localhost:5000/health"
        ;;
    "staging")
        COMPOSE_FILE="docker-compose.yml"
        IMAGE_TAG="staging"
        HEALTH_CHECK_URL="http://localhost:5001/health"
        ;;
    "development")
        COMPOSE_FILE="docker-compose.yml -f docker-compose.override.yml"
        IMAGE_TAG="dev"
        HEALTH_CHECK_URL="http://localhost:5000/health"
        ;;
    *)
        echo "❌ Error: Unknown environment '$ENVIRONMENT'"
        echo "Available environments: production, staging, development"
        exit 1
        ;;
esac

# ===========================================
# UTILITY FUNCTIONS
# ===========================================

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root. Consider using a dedicated deployment user."
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_info "✅ All requirements satisfied"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    local dirs=(
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/reports"
        "$PROJECT_ROOT/data"
        "$BACKUP_DIR"
        "$(dirname "$LOG_FILE")"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    log_info "Performing health check..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_info "✅ Health check passed (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "Health check failed (attempt $attempt/$max_attempts), retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    log_error "❌ Health check failed after $max_attempts attempts"
    return 1
}

# Backup function
backup_current() {
    log_info "Creating backup..."
    
    local backup_name="bot-slack-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup configuration files
    cp "$PROJECT_ROOT/.env" "$backup_path/" 2>/dev/null || log_warn "No .env file to backup"
    cp -r "$PROJECT_ROOT/deployment" "$backup_path/"
    
    # Backup data
    if [[ -d "$PROJECT_ROOT/data" ]]; then
        cp -r "$PROJECT_ROOT/data" "$backup_path/"
    fi
    
    # Create backup info
    cat > "$backup_path/backup_info.txt" << EOF
Backup created: $(date)
Environment: $ENVIRONMENT
Git commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
Docker images:
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep bot-slack || echo "No bot-slack images found")
EOF
    
    log_info "✅ Backup created: $backup_path"
    
    # Cleanup old backups
    cleanup_old_backups
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    local backup_count=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "bot-slack-*" | wc -l)
    
    if [[ $backup_count -gt $MAX_BACKUPS ]]; then
        local to_remove=$((backup_count - MAX_BACKUPS))
        find "$BACKUP_DIR" -maxdepth 1 -type d -name "bot-slack-*" -printf '%T+ %p\n' | \
            sort | head -n "$to_remove" | cut -d' ' -f2- | \
            xargs -r rm -rf
        log_info "Removed $to_remove old backup(s)"
    fi
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    
    cd "$PROJECT_ROOT/deployment"
    
    # Set environment variables for docker-compose
    export IMAGE_TAG="$IMAGE_TAG"
    export CI_REGISTRY_IMAGE="${CI_REGISTRY_IMAGE:-registry.gitlab.com/your-group/bot-slack}"
    
    if docker-compose -f $COMPOSE_FILE pull; then
        log_info "✅ Images pulled successfully"
    else
        log_error "❌ Failed to pull images"
        return 1
    fi
}

# Deploy function
deploy() {
    log_info "🚀 Starting deployment to $ENVIRONMENT environment..."
    
    cd "$PROJECT_ROOT/deployment"
    
    # Set environment variables
    export IMAGE_TAG="$IMAGE_TAG"
    export CI_REGISTRY_IMAGE="${CI_REGISTRY_IMAGE:-registry.gitlab.com/your-group/bot-slack}"
    
    # Stop existing containers gracefully
    log_info "Stopping existing containers..."
    docker-compose -f $COMPOSE_FILE down --timeout 30 || true
    
    # Start new containers
    log_info "Starting new containers..."
    if docker-compose -f $COMPOSE_FILE up -d; then
        log_info "✅ Containers started successfully"
    else
        log_error "❌ Failed to start containers"
        return 1
    fi
    
    # Wait for services to be ready
    sleep 15
    
    # Perform health check
    if health_check; then
        log_info "🎉 Deployment completed successfully!"
        
        # Show running containers
        log_info "Running containers:"
        docker-compose -f $COMPOSE_FILE ps
        
        return 0
    else
        log_error "❌ Deployment failed health check"
        return 1
    fi
}

# Rollback function
rollback() {
    log_info "🔄 Starting rollback..."
    
    cd "$PROJECT_ROOT/deployment"
    
    # Find the latest backup
    local latest_backup=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "bot-slack-*" -printf '%T+ %p\n' | sort -r | head -n1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "❌ No backup found for rollback"
        return 1
    fi
    
    log_info "Rolling back to: $latest_backup"
    
    # Stop current containers
    docker-compose -f $COMPOSE_FILE down --timeout 30 || true
    
    # Restore configuration
    if [[ -f "$latest_backup/.env" ]]; then
        cp "$latest_backup/.env" "$PROJECT_ROOT/"
        log_info "Restored .env file"
    fi
    
    # Restore data
    if [[ -d "$latest_backup/data" ]]; then
        rm -rf "$PROJECT_ROOT/data"
        cp -r "$latest_backup/data" "$PROJECT_ROOT/"
        log_info "Restored data directory"
    fi
    
    # Start containers with previous configuration
    if docker-compose -f $COMPOSE_FILE up -d; then
        log_info "✅ Rollback containers started"
        
        # Health check
        if health_check; then
            log_info "🎉 Rollback completed successfully!"
            return 0
        else
            log_error "❌ Rollback failed health check"
            return 1
        fi
    else
        log_error "❌ Failed to start rollback containers"
        return 1
    fi
}

# Status function
status() {
    log_info "📊 Checking service status..."
    
    cd "$PROJECT_ROOT/deployment"
    
    echo "=== Container Status ==="
    docker-compose -f $COMPOSE_FILE ps
    
    echo "\n=== Container Logs (last 20 lines) ==="
    docker-compose -f $COMPOSE_FILE logs --tail=20
    
    echo "\n=== Health Check ==="
    if health_check; then
        echo "✅ Service is healthy"
    else
        echo "❌ Service is unhealthy"
    fi
    
    echo "\n=== System Resources ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Logs function
logs() {
    log_info "📋 Showing service logs..."
    
    cd "$PROJECT_ROOT/deployment"
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

# Cleanup function
cleanup() {
    log_info "🧹 Cleaning up Docker resources..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    log_info "✅ Cleanup completed"
}

# ===========================================
# MAIN EXECUTION
# ===========================================

main() {
    log_info "=== Bot Slack Deployment Script ==="
    log_info "Environment: $ENVIRONMENT"
    log_info "Action: $ACTION"
    log_info "Script directory: $SCRIPT_DIR"
    log_info "Project root: $PROJECT_ROOT"
    
    # Pre-flight checks
    check_root
    check_requirements
    setup_directories
    
    case $ACTION in
        "deploy")
            backup_current
            pull_images
            deploy
            ;;
        "rollback")
            rollback
            ;;
        "status")
            status
            ;;
        "logs")
            logs
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup_current
            ;;
        "health")
            health_check
            ;;
        *)
            echo "❌ Error: Unknown action '$ACTION'"
            echo "Available actions: deploy, rollback, status, logs, cleanup, backup, health"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"