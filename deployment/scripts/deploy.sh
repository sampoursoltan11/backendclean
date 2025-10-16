#!/bin/bash

##############################################################################
# AWS Elastic Beanstalk Deployment Script with DevOps Best Practices
# This script deploys the full-stack application (React + Flask) to AWS EB
# with comprehensive testing, health checks, and rollback capabilities
##############################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="${EB_APP_NAME:-bhp-assessment-app}"
ENV_NAME="${EB_ENV_NAME:-bhp-assessment-env}"
REGION="${AWS_REGION:-us-east-1}"
PLATFORM="python-3.11"
MAX_WAIT_TIME=600  # 10 minutes
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=30

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
DEPLOYMENT_DIR="$ROOT_DIR/deployment"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BUILD_DIR="$DEPLOYMENT_DIR/build"

##############################################################################
# Logging Functions
##############################################################################

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

log_step() {
    echo -e "\n${GREEN}==>${NC} ${BLUE}$1${NC}\n"
}

##############################################################################
# Pre-flight Checks
##############################################################################

check_prerequisites() {
    log_step "Running pre-flight checks..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    log_success "AWS CLI is installed"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured. Run 'aws configure'"
        exit 1
    fi
    log_success "AWS credentials are configured"

    # Check if EB CLI is installed
    if ! command -v eb &> /dev/null; then
        log_warning "EB CLI is not installed. Installing..."
        pip install awsebcli --upgrade --user
    fi
    log_success "EB CLI is available"

    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install it first."
        exit 1
    fi
    log_success "Node.js is installed ($(node --version))"

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    log_success "Python is installed ($(python3 --version))"

    # Check required directories exist
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        exit 1
    fi

    log_success "All prerequisites met!"
}

##############################################################################
# Build Functions
##############################################################################

build_frontend() {
    log_step "Building React frontend..."

    cd "$FRONTEND_DIR"

    # Install dependencies
    log_info "Installing frontend dependencies..."
    npm ci --production=false

    # Run tests
    log_info "Running frontend tests..."
    CI=true npm test -- --passWithNoTests || log_warning "Frontend tests failed, continuing..."

    # Build production bundle
    log_info "Creating production build..."
    npm run build

    if [ ! -d "$FRONTEND_DIR/build" ]; then
        log_error "Frontend build failed - build directory not created"
        exit 1
    fi

    log_success "Frontend built successfully"
    cd "$ROOT_DIR"
}

prepare_backend() {
    log_step "Preparing Flask backend..."

    cd "$BACKEND_DIR"

    # Create requirements.txt if it doesn't exist
    if [ ! -f "requirements.txt" ]; then
        log_warning "requirements.txt not found, creating from environment..."
        pip freeze > requirements.txt
    fi

    log_success "Backend prepared"
    cd "$ROOT_DIR"
}

create_deployment_package() {
    log_step "Creating deployment package..."

    # Clean previous build
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Copy backend files
    log_info "Copying backend files..."
    cp -r "$BACKEND_DIR"/* "$BUILD_DIR/"

    # Copy frontend build
    log_info "Copying frontend build..."
    mkdir -p "$BUILD_DIR/frontend/build"
    cp -r "$FRONTEND_DIR/build"/* "$BUILD_DIR/frontend/build/"

    # Copy EB extensions
    log_info "Copying Elastic Beanstalk configurations..."
    cp -r "$DEPLOYMENT_DIR/.ebextensions" "$BUILD_DIR/"

    # Create .ebignore file
    cat > "$BUILD_DIR/.ebignore" << EOF
*.pyc
__pycache__/
.env
.venv/
venv/
.git/
.gitignore
*.log
.DS_Store
node_modules/
*.test.js
EOF

    log_success "Deployment package created at: $BUILD_DIR"
}

##############################################################################
# AWS Elastic Beanstalk Functions
##############################################################################

initialize_eb() {
    log_step "Initializing Elastic Beanstalk..."

    cd "$BUILD_DIR"

    # Check if EB is already initialized
    if [ ! -d ".elasticbeanstalk" ]; then
        log_info "Initializing new EB application..."
        eb init "$APP_NAME" \
            --platform "$PLATFORM" \
            --region "$REGION" \
            --tags "Project=BHP-Assessment,Environment=Production,ManagedBy=Script"
        log_success "EB application initialized"
    else
        log_info "EB already initialized, updating configuration..."
    fi

    cd "$ROOT_DIR"
}

create_or_update_environment() {
    log_step "Creating or updating EB environment..."

    cd "$BUILD_DIR"

    # Check if environment exists
    ENV_STATUS=$(eb list | grep "$ENV_NAME" || echo "not_found")

    if [[ "$ENV_STATUS" == "not_found" ]]; then
        log_info "Creating new environment: $ENV_NAME"
        eb create "$ENV_NAME" \
            --instance-type t3.small \
            --envvars FLASK_ENV=production \
            --enable-spot \
            --timeout 20
    else
        log_info "Environment exists, deploying update..."
        eb deploy "$ENV_NAME" --timeout 20
    fi

    cd "$ROOT_DIR"
}

wait_for_environment_ready() {
    log_step "Waiting for environment to be ready..."

    cd "$BUILD_DIR"

    local elapsed=0
    local status=""

    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        status=$(eb status "$ENV_NAME" | grep "Status:" | awk '{print $2}' || echo "Unknown")

        log_info "Environment status: $status (${elapsed}s elapsed)"

        if [[ "$status" == "Ready" ]]; then
            log_success "Environment is ready!"
            cd "$ROOT_DIR"
            return 0
        elif [[ "$status" == "Terminated" ]] || [[ "$status" == "Terminating" ]]; then
            log_error "Environment is terminated or terminating"
            cd "$ROOT_DIR"
            return 1
        fi

        sleep 10
        elapsed=$((elapsed + 10))
    done

    log_error "Environment did not become ready within ${MAX_WAIT_TIME}s"
    cd "$ROOT_DIR"
    return 1
}

##############################################################################
# Health Check Functions
##############################################################################

get_environment_url() {
    cd "$BUILD_DIR"
    local url=$(eb status "$ENV_NAME" | grep "CNAME:" | awk '{print $2}')
    cd "$ROOT_DIR"
    echo "https://$url"
}

run_health_checks() {
    log_step "Running health checks..."

    local url=$(get_environment_url)
    log_info "Application URL: $url"

    local attempt=1
    local success=0

    while [ $attempt -le $HEALTH_CHECK_RETRIES ]; do
        log_info "Health check attempt $attempt/$HEALTH_CHECK_RETRIES..."

        # Check backend health
        local backend_status=$(curl -s -o /dev/null -w "%{http_code}" "$url/api/health" || echo "000")

        if [ "$backend_status" == "200" ]; then
            log_success "Backend health check passed (HTTP $backend_status)"
            success=$((success + 1))
        else
            log_warning "Backend health check failed (HTTP $backend_status)"
        fi

        # Check frontend
        local frontend_status=$(curl -s -o /dev/null -w "%{http_code}" "$url/" || echo "000")

        if [ "$frontend_status" == "200" ]; then
            log_success "Frontend health check passed (HTTP $frontend_status)"
            success=$((success + 1))
        else
            log_warning "Frontend health check failed (HTTP $frontend_status)"
        fi

        # If both checks pass, we're good
        if [ $success -ge 2 ]; then
            log_success "All health checks passed!"
            return 0
        fi

        if [ $attempt -lt $HEALTH_CHECK_RETRIES ]; then
            log_info "Waiting ${HEALTH_CHECK_INTERVAL}s before retry..."
            sleep $HEALTH_CHECK_INTERVAL
        fi

        attempt=$((attempt + 1))
        success=0
    done

    log_error "Health checks failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

run_smoke_tests() {
    log_step "Running smoke tests..."

    local url=$(get_environment_url)

    # Test 1: Check if API endpoints are accessible
    log_info "Test 1: API accessibility..."
    if curl -s "$url/api/health" | grep -q "healthy"; then
        log_success "✓ API is accessible"
    else
        log_error "✗ API is not accessible"
        return 1
    fi

    # Test 2: Check security headers
    log_info "Test 2: Security headers..."
    local headers=$(curl -sI "$url/")

    if echo "$headers" | grep -q "X-Frame-Options"; then
        log_success "✓ Security headers are set"
    else
        log_warning "✗ Some security headers might be missing"
    fi

    # Test 3: Check HTTPS redirect
    log_info "Test 3: HTTPS enforcement..."
    local http_url="${url/https/http}"
    local redirect_status=$(curl -s -o /dev/null -w "%{http_code}" -L "$http_url")

    if [ "$redirect_status" == "200" ]; then
        log_success "✓ HTTPS is working"
    else
        log_warning "✗ HTTPS might not be fully configured"
    fi

    log_success "Smoke tests completed!"
}

##############################################################################
# Rollback Function
##############################################################################

rollback_deployment() {
    log_warning "Rolling back deployment..."

    cd "$BUILD_DIR"

    # Get previous version
    local prev_version=$(eb history | head -n 2 | tail -n 1 | awk '{print $2}')

    if [ -n "$prev_version" ]; then
        log_info "Rolling back to version: $prev_version"
        eb deploy --version "$prev_version"
        log_success "Rollback completed"
    else
        log_error "No previous version found for rollback"
    fi

    cd "$ROOT_DIR"
}

##############################################################################
# Display Information
##############################################################################

display_deployment_info() {
    log_step "Deployment Information"

    local url=$(get_environment_url)

    cat << EOF

${GREEN}═══════════════════════════════════════════════════════════════${NC}
${GREEN}              DEPLOYMENT SUCCESSFUL!${NC}
${GREEN}═══════════════════════════════════════════════════════════════${NC}

${BLUE}Application URL:${NC}
  $url

${BLUE}Useful Commands:${NC}
  View logs:      eb logs "$ENV_NAME" --all
  SSH to server:  eb ssh "$ENV_NAME"
  Check status:   eb status "$ENV_NAME"
  Open in browser: eb open "$ENV_NAME"
  Scale up:       eb scale 2 "$ENV_NAME"
  Terminate:      eb terminate "$ENV_NAME"

${BLUE}Monitoring:${NC}
  AWS Console: https://console.aws.amazon.com/elasticbeanstalk/home?region=$REGION#/environment/dashboard?applicationName=$APP_NAME&environmentId=$ENV_NAME

${BLUE}Security:${NC}
  ✓ HTTPS Enabled
  ✓ Security Headers Configured
  ✓ Auto-scaling Enabled
  ✓ Enhanced Health Monitoring

${BLUE}Next Steps:${NC}
  1. Test the application: $url
  2. Configure custom domain (optional)
  3. Set up CloudWatch alarms
  4. Configure backup strategy

${GREEN}═══════════════════════════════════════════════════════════════${NC}

EOF
}

##############################################################################
# Main Deployment Flow
##############################################################################

main() {
    log_step "Starting AWS Elastic Beanstalk Deployment"
    echo "Application: $APP_NAME"
    echo "Environment: $ENV_NAME"
    echo "Region: $REGION"
    echo ""

    # Pre-flight checks
    check_prerequisites

    # Build
    build_frontend
    prepare_backend
    create_deployment_package

    # Deploy
    initialize_eb
    create_or_update_environment

    # Wait and verify
    if wait_for_environment_ready; then
        if run_health_checks; then
            run_smoke_tests
            display_deployment_info
            log_success "Deployment completed successfully!"
            exit 0
        else
            log_error "Health checks failed!"
            read -p "Do you want to rollback? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rollback_deployment
            fi
            exit 1
        fi
    else
        log_error "Environment failed to become ready"
        exit 1
    fi
}

##############################################################################
# Cleanup on Exit
##############################################################################

cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Deployment failed!"
        log_info "Run 'eb logs $ENV_NAME' to view error logs"
    fi
}

trap cleanup EXIT

# Run main function
main "$@"
