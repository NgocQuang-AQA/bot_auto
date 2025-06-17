#!/bin/bash
# Build script for Bot Slack Service CI/CD Pipeline
# This script handles Docker image building, tagging, and pushing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
IMAGE_NAME=${IMAGE_NAME:-"bot-slack"}
REGISTRY=${CI_REGISTRY:-"registry.gitlab.com"}
REGISTRY_USER=${CI_REGISTRY_USER:-""}
REGISTRY_PASSWORD=${CI_REGISTRY_PASSWORD:-""}
PROJECT_PATH=${CI_PROJECT_PATH:-""}
COMMIT_SHA=${CI_COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || echo "unknown")}
COMMIT_REF_NAME=${CI_COMMIT_REF_NAME:-$(git branch --show-current 2>/dev/null || echo "unknown")}
PIPELINE_ID=${CI_PIPELINE_ID:-"local"}
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
DOCKERFILE_PATH=${DOCKERFILE_PATH:-"deployment/Dockerfile"}
BUILD_CONTEXT=${BUILD_CONTEXT:-"."}
PUSH_IMAGE=${PUSH_IMAGE:-"true"}
BUILD_ARGS=${BUILD_ARGS:-""}
PLATFORM=${PLATFORM:-"linux/amd64"}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment
validate_environment() {
    log_info "Validating build environment..."
    
    # Check if Docker is available
    if ! command_exists docker; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Dockerfile exists
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        log_error "Dockerfile not found at: $DOCKERFILE_PATH"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Environment validation completed"
}

# Function to login to registry
registry_login() {
    if [ "$PUSH_IMAGE" = "true" ] && [ -n "$REGISTRY_USER" ] && [ -n "$REGISTRY_PASSWORD" ]; then
        log_info "Logging into registry: $REGISTRY"
        echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY" -u "$REGISTRY_USER" --password-stdin
        log_success "Registry login successful"
    else
        log_warning "Skipping registry login (missing credentials or push disabled)"
    fi
}

# Function to generate image tags
generate_tags() {
    local base_image="$REGISTRY/$PROJECT_PATH/$IMAGE_NAME"
    
    # Always include commit SHA
    TAGS=("$base_image:$COMMIT_SHA")
    
    # Add branch-based tags
    if [ "$COMMIT_REF_NAME" = "main" ] || [ "$COMMIT_REF_NAME" = "master" ]; then
        TAGS+=("$base_image:latest")
        TAGS+=("$base_image:stable")
    elif [ "$COMMIT_REF_NAME" = "develop" ]; then
        TAGS+=("$base_image:develop")
    else
        # For feature branches, use sanitized branch name
        SANITIZED_BRANCH=$(echo "$COMMIT_REF_NAME" | sed 's/[^a-zA-Z0-9._-]/-/g' | tr '[:upper:]' '[:lower:]')
        TAGS+=("$base_image:$SANITIZED_BRANCH")
    fi
    
    # Add pipeline ID tag
    TAGS+=("$base_image:pipeline-$PIPELINE_ID")
    
    # Add version tag if VERSION is set
    if [ -n "$VERSION" ]; then
        TAGS+=("$base_image:$VERSION")
        TAGS+=("$base_image:v$VERSION")
    fi
    
    log_info "Generated tags:"
    for tag in "${TAGS[@]}"; do
        echo "  - $tag"
    done
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image..."
    
    # Prepare build arguments
    local build_args_array=()
    
    # Add default build args
    build_args_array+=("--build-arg" "BUILD_DATE=$BUILD_DATE")
    build_args_array+=("--build-arg" "VCS_REF=$COMMIT_SHA")
    build_args_array+=("--build-arg" "VERSION=${VERSION:-$COMMIT_SHA}")
    build_args_array+=("--build-arg" "PIPELINE_ID=$PIPELINE_ID")
    
    # Add custom build args
    if [ -n "$BUILD_ARGS" ]; then
        IFS=',' read -ra ADDR <<< "$BUILD_ARGS"
        for arg in "${ADDR[@]}"; do
            build_args_array+=("--build-arg" "$arg")
        done
    fi
    
    # Add labels
    local labels=(
        "--label" "org.opencontainers.image.created=$BUILD_DATE"
        "--label" "org.opencontainers.image.source=$CI_PROJECT_URL"
        "--label" "org.opencontainers.image.version=${VERSION:-$COMMIT_SHA}"
        "--label" "org.opencontainers.image.revision=$COMMIT_SHA"
        "--label" "org.opencontainers.image.title=Bot Slack Service"
        "--label" "org.opencontainers.image.description=Automated Slack bot for project management"
        "--label" "pipeline.id=$PIPELINE_ID"
        "--label" "pipeline.url=$CI_PIPELINE_URL"
        "--label" "commit.branch=$COMMIT_REF_NAME"
    )
    
    # Build the image with the first tag
    local primary_tag="${TAGS[0]}"
    
    docker build \
        --platform "$PLATFORM" \
        --file "$DOCKERFILE_PATH" \
        "${build_args_array[@]}" \
        "${labels[@]}" \
        --tag "$primary_tag" \
        "$BUILD_CONTEXT"
    
    log_success "Docker image built successfully: $primary_tag"
    
    # Tag the image with additional tags
    for tag in "${TAGS[@]:1}"; do
        log_info "Tagging image: $tag"
        docker tag "$primary_tag" "$tag"
    done
    
    log_success "Image tagging completed"
}

# Function to scan image for vulnerabilities
scan_image() {
    log_info "Scanning image for vulnerabilities..."
    
    local primary_tag="${TAGS[0]}"
    
    # Try different vulnerability scanners
    if command_exists trivy; then
        log_info "Running Trivy security scan..."
        trivy image --format json --output "security-scan.json" "$primary_tag" || true
        trivy image --format table "$primary_tag" || true
    elif command_exists docker; then
        # Use Docker Scout if available
        if docker scout version >/dev/null 2>&1; then
            log_info "Running Docker Scout security scan..."
            docker scout cves "$primary_tag" || true
        else
            log_warning "No vulnerability scanner available"
        fi
    else
        log_warning "No vulnerability scanner available"
    fi
    
    log_success "Security scan completed"
}

# Function to test image
test_image() {
    log_info "Testing Docker image..."
    
    local primary_tag="${TAGS[0]}"
    
    # Basic smoke test
    log_info "Running smoke test..."
    docker run --rm "$primary_tag" python --version
    
    # Health check test
    log_info "Testing health check..."
    local container_id
    container_id=$(docker run -d -p 5000:5000 "$primary_tag")
    
    # Wait for container to start
    sleep 10
    
    # Check if health endpoint responds
    if command_exists curl; then
        if curl -f http://localhost:5000/health >/dev/null 2>&1; then
            log_success "Health check passed"
        else
            log_warning "Health check failed or endpoint not available"
        fi
    else
        log_warning "curl not available, skipping health check"
    fi
    
    # Cleanup test container
    docker stop "$container_id" >/dev/null 2>&1 || true
    docker rm "$container_id" >/dev/null 2>&1 || true
    
    log_success "Image testing completed"
}

# Function to push images
push_images() {
    if [ "$PUSH_IMAGE" = "true" ]; then
        log_info "Pushing images to registry..."
        
        for tag in "${TAGS[@]}"; do
            log_info "Pushing: $tag"
            docker push "$tag"
        done
        
        log_success "All images pushed successfully"
    else
        log_info "Image push disabled, skipping..."
    fi
}

# Function to cleanup local images
cleanup_images() {
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        log_info "Cleaning up local images..."
        
        for tag in "${TAGS[@]}"; do
            docker rmi "$tag" >/dev/null 2>&1 || true
        done
        
        # Clean up dangling images
        docker image prune -f >/dev/null 2>&1 || true
        
        log_success "Image cleanup completed"
    fi
}

# Function to generate build report
generate_build_report() {
    log_info "Generating build report..."
    
    local report_file="build-report.json"
    
    cat > "$report_file" << EOF
{
  "build_info": {
    "image_name": "$IMAGE_NAME",
    "build_date": "$BUILD_DATE",
    "commit_sha": "$COMMIT_SHA",
    "commit_ref": "$COMMIT_REF_NAME",
    "pipeline_id": "$PIPELINE_ID",
    "platform": "$PLATFORM",
    "dockerfile": "$DOCKERFILE_PATH"
  },
  "tags": [
EOF
    
    for i in "${!TAGS[@]}"; do
        if [ $i -eq $((${#TAGS[@]} - 1)) ]; then
            echo "    \"${TAGS[$i]}\"" >> "$report_file"
        else
            echo "    \"${TAGS[$i]}\"," >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF
  ],
  "registry": "$REGISTRY",
  "pushed": $PUSH_IMAGE
}
EOF
    
    log_success "Build report generated: $report_file"
}

# Function to display build summary
display_summary() {
    log_info "Build Summary:"
    echo "=========================================="
    echo "Image Name: $IMAGE_NAME"
    echo "Build Date: $BUILD_DATE"
    echo "Commit SHA: $COMMIT_SHA"
    echo "Branch: $COMMIT_REF_NAME"
    echo "Pipeline ID: $PIPELINE_ID"
    echo "Platform: $PLATFORM"
    echo "Tags Created: ${#TAGS[@]}"
    echo "Pushed to Registry: $PUSH_IMAGE"
    echo "=========================================="
}

# Main execution
main() {
    log_info "Starting Docker build process..."
    
    validate_environment
    registry_login
    generate_tags
    build_image
    scan_image
    test_image
    push_images
    generate_build_report
    cleanup_images
    display_summary
    
    log_success "Build process completed successfully"
}

# Trap to ensure cleanup on exit
trap 'log_info "Build process interrupted"' INT TERM

# Run main function
main "$@"