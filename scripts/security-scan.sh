#!/bin/bash
# Security scanning script for Bot Slack Service CI/CD Pipeline
# This script performs comprehensive security analysis including dependency, code, and container scanning

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
SCAN_TYPE=${1:-"all"}
REPORTS_DIR="security-reports"
IMAGE_NAME=${IMAGE_NAME:-"bot-slack"}
REGISTRY=${CI_REGISTRY:-"registry.gitlab.com"}
PROJECT_PATH=${CI_PROJECT_PATH:-""}
COMMIT_SHA=${CI_COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || echo "unknown")}
FAIL_ON_HIGH=${FAIL_ON_HIGH:-"true"}
FAIL_ON_CRITICAL=${FAIL_ON_CRITICAL:-"true"}
MAX_VULNERABILITIES=${MAX_VULNERABILITIES:-10}

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install security tools
install_security_tools() {
    log_info "Installing security scanning tools..."
    
    # Install Python security tools
    pip install --quiet bandit safety semgrep pip-audit
    
    # Install Trivy if not available
    if ! command_exists trivy; then
        log_info "Installing Trivy..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install trivy
        else
            log_warning "Trivy installation not supported on this OS"
        fi
    fi
    
    # Install Grype if not available
    if ! command_exists grype; then
        log_info "Installing Grype..."
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    fi
    
    log_success "Security tools installation completed"
}

# Function to scan Python dependencies
scan_dependencies() {
    log_info "Scanning Python dependencies for vulnerabilities..."
    
    # Safety check
    if command_exists safety; then
        log_info "Running Safety dependency scan..."
        safety check --json --output "$REPORTS_DIR/safety-report.json" || true
        safety check --output "$REPORTS_DIR/safety-report.txt" || true
        log_success "Safety scan completed"
    fi
    
    # pip-audit check
    if command_exists pip-audit; then
        log_info "Running pip-audit dependency scan..."
        pip-audit --format=json --output="$REPORTS_DIR/pip-audit-report.json" || true
        pip-audit --format=cyclonedx-json --output="$REPORTS_DIR/pip-audit-sbom.json" || true
        pip-audit --output="$REPORTS_DIR/pip-audit-report.txt" || true
        log_success "pip-audit scan completed"
    fi
    
    # Generate dependency tree
    if command_exists pipdeptree; then
        log_info "Generating dependency tree..."
        pipdeptree --json > "$REPORTS_DIR/dependency-tree.json"
        pipdeptree > "$REPORTS_DIR/dependency-tree.txt"
        log_success "Dependency tree generated"
    fi
    
    log_success "Dependency scanning completed"
}

# Function to scan source code
scan_source_code() {
    log_info "Scanning source code for security issues..."
    
    # Bandit security linting
    if command_exists bandit; then
        log_info "Running Bandit security analysis..."
        bandit -r app/ services/ utils/ config/ -f json -o "$REPORTS_DIR/bandit-report.json" || true
        bandit -r app/ services/ utils/ config/ -f html -o "$REPORTS_DIR/bandit-report.html" || true
        bandit -r app/ services/ utils/ config/ -f txt -o "$REPORTS_DIR/bandit-report.txt" || true
        log_success "Bandit scan completed"
    fi
    
    # Semgrep security analysis
    if command_exists semgrep; then
        log_info "Running Semgrep security analysis..."
        semgrep --config=auto --json --output="$REPORTS_DIR/semgrep-report.json" app/ services/ utils/ config/ || true
        semgrep --config=auto --output="$REPORTS_DIR/semgrep-report.txt" app/ services/ utils/ config/ || true
        log_success "Semgrep scan completed"
    fi
    
    # Check for secrets in code
    log_info "Scanning for secrets and sensitive data..."
    if command_exists git; then
        # Use git to find potential secrets
        git log --all --full-history --grep="password\|secret\|key\|token" --oneline > "$REPORTS_DIR/potential-secrets-commits.txt" 2>/dev/null || true
        
        # Search for common secret patterns in files
        grep -r -i -E "(password|secret|key|token|api_key)\s*=\s*['\"][^'\"]{8,}['\"]" app/ services/ utils/ config/ > "$REPORTS_DIR/potential-secrets-files.txt" 2>/dev/null || true
    fi
    
    log_success "Source code scanning completed"
}

# Function to scan Docker image
scan_docker_image() {
    local image_tag="$REGISTRY/$PROJECT_PATH/$IMAGE_NAME:$COMMIT_SHA"
    
    log_info "Scanning Docker image for vulnerabilities: $image_tag"
    
    # Trivy container scan
    if command_exists trivy; then
        log_info "Running Trivy container scan..."
        trivy image --format json --output "$REPORTS_DIR/trivy-image-report.json" "$image_tag" || true
        trivy image --format table --output "$REPORTS_DIR/trivy-image-report.txt" "$image_tag" || true
        trivy image --format sarif --output "$REPORTS_DIR/trivy-image-report.sarif" "$image_tag" || true
        
        # Scan for misconfigurations
        trivy config --format json --output "$REPORTS_DIR/trivy-config-report.json" deployment/ || true
        trivy config --format table --output "$REPORTS_DIR/trivy-config-report.txt" deployment/ || true
        
        log_success "Trivy scan completed"
    fi
    
    # Grype container scan
    if command_exists grype; then
        log_info "Running Grype container scan..."
        grype "$image_tag" -o json > "$REPORTS_DIR/grype-report.json" || true
        grype "$image_tag" -o table > "$REPORTS_DIR/grype-report.txt" || true
        grype "$image_tag" -o sarif > "$REPORTS_DIR/grype-report.sarif" || true
        log_success "Grype scan completed"
    fi
    
    # Docker Scout scan (if available)
    if docker scout version >/dev/null 2>&1; then
        log_info "Running Docker Scout scan..."
        docker scout cves "$image_tag" --format sarif --output "$REPORTS_DIR/docker-scout-report.sarif" || true
        docker scout cves "$image_tag" --format json --output "$REPORTS_DIR/docker-scout-report.json" || true
        docker scout cves "$image_tag" > "$REPORTS_DIR/docker-scout-report.txt" || true
        log_success "Docker Scout scan completed"
    fi
    
    log_success "Docker image scanning completed"
}

# Function to scan infrastructure as code
scan_infrastructure() {
    log_info "Scanning infrastructure as code..."
    
    # Scan Docker files
    if command_exists trivy; then
        log_info "Scanning Dockerfile with Trivy..."
        trivy config --format json --output "$REPORTS_DIR/dockerfile-scan.json" deployment/Dockerfile || true
        trivy config --format table --output "$REPORTS_DIR/dockerfile-scan.txt" deployment/Dockerfile || true
    fi
    
    # Scan Docker Compose files
    if [ -f "deployment/docker-compose.yml" ]; then
        log_info "Scanning Docker Compose configuration..."
        if command_exists trivy; then
            trivy config --format json --output "$REPORTS_DIR/docker-compose-scan.json" deployment/docker-compose.yml || true
            trivy config --format table --output "$REPORTS_DIR/docker-compose-scan.txt" deployment/docker-compose.yml || true
        fi
    fi
    
    # Scan GitLab CI configuration
    if [ -f ".gitlab-ci.yml" ]; then
        log_info "Scanning GitLab CI configuration..."
        if command_exists trivy; then
            trivy config --format json --output "$REPORTS_DIR/gitlab-ci-scan.json" .gitlab-ci.yml || true
            trivy config --format table --output "$REPORTS_DIR/gitlab-ci-scan.txt" .gitlab-ci.yml || true
        fi
    fi
    
    log_success "Infrastructure scanning completed"
}

# Function to analyze scan results
analyze_results() {
    log_info "Analyzing security scan results..."
    
    local critical_count=0
    local high_count=0
    local medium_count=0
    local low_count=0
    local total_count=0
    
    # Analyze Trivy results
    if [ -f "$REPORTS_DIR/trivy-image-report.json" ]; then
        if command_exists jq; then
            critical_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$REPORTS_DIR/trivy-image-report.json" 2>/dev/null || echo 0)
            high_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$REPORTS_DIR/trivy-image-report.json" 2>/dev/null || echo 0)
            medium_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "MEDIUM")] | length' "$REPORTS_DIR/trivy-image-report.json" 2>/dev/null || echo 0)
            low_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "LOW")] | length' "$REPORTS_DIR/trivy-image-report.json" 2>/dev/null || echo 0)
        fi
    fi
    
    total_count=$((critical_count + high_count + medium_count + low_count))
    
    # Generate summary report
    cat > "$REPORTS_DIR/security-summary.json" << EOF
{
  "scan_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "commit_sha": "$COMMIT_SHA",
  "image_tag": "$REGISTRY/$PROJECT_PATH/$IMAGE_NAME:$COMMIT_SHA",
  "vulnerability_summary": {
    "critical": $critical_count,
    "high": $high_count,
    "medium": $medium_count,
    "low": $low_count,
    "total": $total_count
  },
  "scan_types": [
    "dependency_scan",
    "source_code_scan",
    "container_scan",
    "infrastructure_scan"
  ],
  "tools_used": [
    "bandit",
    "safety",
    "pip-audit",
    "trivy",
    "grype",
    "semgrep"
  ]
}
EOF
    
    # Check if we should fail the build
    local should_fail=false
    
    if [ "$FAIL_ON_CRITICAL" = "true" ] && [ "$critical_count" -gt 0 ]; then
        log_error "Found $critical_count critical vulnerabilities"
        should_fail=true
    fi
    
    if [ "$FAIL_ON_HIGH" = "true" ] && [ "$high_count" -gt 0 ]; then
        log_error "Found $high_count high severity vulnerabilities"
        should_fail=true
    fi
    
    if [ "$total_count" -gt "$MAX_VULNERABILITIES" ]; then
        log_error "Total vulnerabilities ($total_count) exceed maximum allowed ($MAX_VULNERABILITIES)"
        should_fail=true
    fi
    
    if [ "$should_fail" = "true" ]; then
        log_error "Security scan failed due to policy violations"
        return 1
    fi
    
    log_success "Security analysis completed successfully"
}

# Function to generate security report
generate_security_report() {
    log_info "Generating comprehensive security report..."
    
    local report_file="$REPORTS_DIR/security-report.html"
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        .summary-table { width: 100%; border-collapse: collapse; }
        .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .summary-table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Scan Report</h1>
        <p><strong>Scan Date:</strong> $(date)</p>
        <p><strong>Commit SHA:</strong> $COMMIT_SHA</p>
        <p><strong>Image:</strong> $REGISTRY/$PROJECT_PATH/$IMAGE_NAME:$COMMIT_SHA</p>
    </div>
EOF
    
    # Add vulnerability summary if available
    if [ -f "$REPORTS_DIR/security-summary.json" ]; then
        cat >> "$report_file" << 'EOF'
    <div class="section">
        <h2>Vulnerability Summary</h2>
        <table class="summary-table">
            <tr><th>Severity</th><th>Count</th></tr>
EOF
        
        if command_exists jq; then
            local critical=$(jq -r '.vulnerability_summary.critical' "$REPORTS_DIR/security-summary.json")
            local high=$(jq -r '.vulnerability_summary.high' "$REPORTS_DIR/security-summary.json")
            local medium=$(jq -r '.vulnerability_summary.medium' "$REPORTS_DIR/security-summary.json")
            local low=$(jq -r '.vulnerability_summary.low' "$REPORTS_DIR/security-summary.json")
            
            echo "            <tr><td class='critical'>Critical</td><td>$critical</td></tr>" >> "$report_file"
            echo "            <tr><td class='high'>High</td><td>$high</td></tr>" >> "$report_file"
            echo "            <tr><td class='medium'>Medium</td><td>$medium</td></tr>" >> "$report_file"
            echo "            <tr><td class='low'>Low</td><td>$low</td></tr>" >> "$report_file"
        fi
        
        cat >> "$report_file" << 'EOF'
        </table>
    </div>
EOF
    fi
    
    # Add links to detailed reports
    cat >> "$report_file" << 'EOF'
    <div class="section">
        <h2>Detailed Reports</h2>
        <ul>
EOF
    
    for report in "$REPORTS_DIR"/*.json "$REPORTS_DIR"/*.txt "$REPORTS_DIR"/*.html; do
        if [ -f "$report" ] && [ "$(basename "$report")" != "security-report.html" ]; then
            echo "            <li><a href='$(basename "$report")'>$(basename "$report")</a></li>" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << 'EOF'
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "Security report generated: $report_file"
}

# Function to upload reports to GitLab
upload_reports() {
    if [ "$CI" = "true" ] && [ -n "$CI_JOB_TOKEN" ]; then
        log_info "Uploading security reports to GitLab..."
        
        # Create artifacts
        tar -czf security-reports.tar.gz "$REPORTS_DIR"/
        
        log_success "Security reports packaged for GitLab artifacts"
    else
        log_info "Not in CI environment, skipping report upload"
    fi
}

# Function to run all security scans
run_all_scans() {
    log_info "Running all security scans..."
    
    scan_dependencies
    scan_source_code
    scan_docker_image
    scan_infrastructure
    analyze_results
    generate_security_report
    upload_reports
    
    log_success "All security scans completed"
}

# Function to display scan summary
display_summary() {
    log_info "Security Scan Summary:"
    echo "=========================================="
    
    if [ -f "$REPORTS_DIR/security-summary.json" ] && command_exists jq; then
        local critical=$(jq -r '.vulnerability_summary.critical' "$REPORTS_DIR/security-summary.json")
        local high=$(jq -r '.vulnerability_summary.high' "$REPORTS_DIR/security-summary.json")
        local medium=$(jq -r '.vulnerability_summary.medium' "$REPORTS_DIR/security-summary.json")
        local low=$(jq -r '.vulnerability_summary.low' "$REPORTS_DIR/security-summary.json")
        local total=$(jq -r '.vulnerability_summary.total' "$REPORTS_DIR/security-summary.json")
        
        echo "Critical Vulnerabilities: $critical"
        echo "High Vulnerabilities: $high"
        echo "Medium Vulnerabilities: $medium"
        echo "Low Vulnerabilities: $low"
        echo "Total Vulnerabilities: $total"
    fi
    
    echo "Reports Directory: $REPORTS_DIR"
    echo "Scan Types: $SCAN_TYPE"
    echo "=========================================="
}

# Main execution
main() {
    log_info "Starting security scanning with type: $SCAN_TYPE"
    
    # Install tools if not in CI
    if [ "$CI" != "true" ]; then
        install_security_tools
    fi
    
    case "$SCAN_TYPE" in
        "dependencies")
            scan_dependencies
            ;;
        "source")
            scan_source_code
            ;;
        "container")
            scan_docker_image
            ;;
        "infrastructure")
            scan_infrastructure
            ;;
        "all")
            run_all_scans
            ;;
        *)
            log_error "Unknown scan type: $SCAN_TYPE"
            echo "Available types: dependencies, source, container, infrastructure, all"
            exit 1
            ;;
    esac
    
    if [ "$SCAN_TYPE" != "all" ]; then
        analyze_results
        generate_security_report
        upload_reports
    fi
    
    display_summary
    
    log_success "Security scanning completed successfully"
}

# Trap to ensure cleanup on exit
trap 'log_info "Security scan interrupted"' INT TERM

# Run main function
main "$@"