#!/bin/bash
# Test script for Bot Slack Service CI/CD Pipeline
# This script runs comprehensive tests including unit, integration, and code quality checks

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
TEST_TYPE=${1:-"all"}
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
TEST_RESULTS_DIR="test-results"
COVERAGE_DIR="coverage"
REPORTS_DIR="reports"

# Create directories
mkdir -p "$TEST_RESULTS_DIR" "$COVERAGE_DIR" "$REPORTS_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
install_dependencies() {
    log_info "Installing test dependencies..."
    
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    else
        log_warning "requirements-dev.txt not found, installing basic test dependencies"
        pip install pytest pytest-cov pytest-flask pytest-mock flake8 black isort mypy bandit safety
    fi
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    log_success "Dependencies installed"
}

# Function to run unit tests
run_unit_tests() {
    log_info "Running unit tests..."
    
    pytest tests/unit/ \
        --verbose \
        --tb=short \
        --cov=app \
        --cov=services \
        --cov=utils \
        --cov=config \
        --cov-report=html:"$COVERAGE_DIR/html" \
        --cov-report=xml:"$COVERAGE_DIR/coverage.xml" \
        --cov-report=term-missing \
        --cov-fail-under="$COVERAGE_THRESHOLD" \
        --junit-xml="$TEST_RESULTS_DIR/unit-tests.xml" \
        --html="$TEST_RESULTS_DIR/unit-tests.html" \
        --self-contained-html
    
    log_success "Unit tests completed"
}

# Function to run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    # Set test environment variables
    export FLASK_ENV=testing
    export TESTING=true
    
    pytest tests/integration/ \
        --verbose \
        --tb=short \
        --junit-xml="$TEST_RESULTS_DIR/integration-tests.xml" \
        --html="$TEST_RESULTS_DIR/integration-tests.html" \
        --self-contained-html
    
    log_success "Integration tests completed"
}

# Function to run end-to-end tests
run_e2e_tests() {
    log_info "Running end-to-end tests..."
    
    if [ -d "tests/e2e" ]; then
        pytest tests/e2e/ \
            --verbose \
            --tb=short \
            --junit-xml="$TEST_RESULTS_DIR/e2e-tests.xml" \
            --html="$TEST_RESULTS_DIR/e2e-tests.html" \
            --self-contained-html
        
        log_success "End-to-end tests completed"
    else
        log_warning "No end-to-end tests found"
    fi
}

# Function to run code quality checks
run_code_quality() {
    log_info "Running code quality checks..."
    
    # Flake8 linting
    log_info "Running flake8 linting..."
    flake8 app/ services/ utils/ config/ --output-file="$REPORTS_DIR/flake8-report.txt" --format=html --htmldir="$REPORTS_DIR/flake8-html" || true
    
    # Black formatting check
    log_info "Checking code formatting with black..."
    black --check --diff app/ services/ utils/ config/ > "$REPORTS_DIR/black-report.txt" || true
    
    # Import sorting check
    log_info "Checking import sorting with isort..."
    isort --check-only --diff app/ services/ utils/ config/ > "$REPORTS_DIR/isort-report.txt" || true
    
    # Type checking
    log_info "Running type checking with mypy..."
    mypy app/ services/ utils/ config/ --html-report "$REPORTS_DIR/mypy-html" --txt-report "$REPORTS_DIR/mypy-txt" || true
    
    log_success "Code quality checks completed"
}

# Function to run security checks
run_security_checks() {
    log_info "Running security checks..."
    
    # Bandit security linting
    log_info "Running bandit security analysis..."
    bandit -r app/ services/ utils/ config/ -f json -o "$REPORTS_DIR/bandit-report.json" || true
    bandit -r app/ services/ utils/ config/ -f html -o "$REPORTS_DIR/bandit-report.html" || true
    
    # Safety dependency check
    log_info "Checking dependencies for known vulnerabilities..."
    safety check --json --output "$REPORTS_DIR/safety-report.json" || true
    
    log_success "Security checks completed"
}

# Function to run performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    if [ -d "tests/performance" ]; then
        pytest tests/performance/ \
            --verbose \
            --tb=short \
            --junit-xml="$TEST_RESULTS_DIR/performance-tests.xml" \
            --html="$TEST_RESULTS_DIR/performance-tests.html" \
            --self-contained-html
        
        log_success "Performance tests completed"
    else
        log_warning "No performance tests found"
    fi
}

# Function to generate coverage badge
generate_coverage_badge() {
    log_info "Generating coverage badge..."
    
    if command_exists coverage-badge; then
        coverage-badge -o "$COVERAGE_DIR/coverage-badge.svg"
        log_success "Coverage badge generated"
    else
        log_warning "coverage-badge not installed, skipping badge generation"
    fi
}

# Function to run all tests
run_all_tests() {
    log_info "Running all tests..."
    
    run_unit_tests
    run_integration_tests
    run_e2e_tests
    run_performance_tests
    run_code_quality
    run_security_checks
    generate_coverage_badge
    
    log_success "All tests completed"
}

# Function to clean up test artifacts
cleanup() {
    log_info "Cleaning up test artifacts..."
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    # Remove pytest cache
    rm -rf .pytest_cache 2>/dev/null || true
    
    # Remove coverage cache
    rm -f .coverage 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Function to display test summary
display_summary() {
    log_info "Test Summary:"
    echo "=========================================="
    
    if [ -f "$COVERAGE_DIR/coverage.xml" ]; then
        COVERAGE=$(grep -o 'line-rate="[^"]*"' "$COVERAGE_DIR/coverage.xml" | head -1 | cut -d'"' -f2)
        COVERAGE_PERCENT=$(echo "$COVERAGE * 100" | bc -l | cut -d'.' -f1)
        echo "Coverage: ${COVERAGE_PERCENT}%"
    fi
    
    if [ -d "$TEST_RESULTS_DIR" ]; then
        echo "Test results available in: $TEST_RESULTS_DIR"
    fi
    
    if [ -d "$COVERAGE_DIR" ]; then
        echo "Coverage reports available in: $COVERAGE_DIR"
    fi
    
    if [ -d "$REPORTS_DIR" ]; then
        echo "Quality reports available in: $REPORTS_DIR"
    fi
    
    echo "=========================================="
}

# Main execution
main() {
    log_info "Starting test execution with type: $TEST_TYPE"
    
    # Install dependencies if not in CI
    if [ "$CI" != "true" ]; then
        install_dependencies
    fi
    
    case "$TEST_TYPE" in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "quality")
            run_code_quality
            ;;
        "security")
            run_security_checks
            ;;
        "all")
            run_all_tests
            ;;
        *)
            log_error "Unknown test type: $TEST_TYPE"
            echo "Available types: unit, integration, e2e, performance, quality, security, all"
            exit 1
            ;;
    esac
    
    generate_coverage_badge
    display_summary
    
    log_success "Test execution completed successfully"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"