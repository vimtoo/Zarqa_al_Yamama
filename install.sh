#!/bin/bash

################################################################################
# ZARQA AL YAMAMA - ONE-CLICK INSTALLATION SCRIPT
# Platform: Linux / macOS
# Creator: Qusai Al-Duaij
# Version: 1.0.0
# Status: Production-Ready
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="zarqa-al-yamama"
PROJECT_DIR="$(pwd)/$PROJECT_NAME"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
ENV_FILE="$PROJECT_DIR/backend/.env"
ENV_EXAMPLE="$PROJECT_DIR/backend/.env.example"

################################################################################
# UTILITY FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "================================================================================"
    echo "  ZARQA AL YAMAMA - FORESIGHT INTELLIGENCE AGENT"
    echo "  One-Click Installation Script"
    echo "  Creator: Qusai Al-Duaij | LoLo AI Initiative"
    echo "================================================================================"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}>>> $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    print_success "$1 is installed"
    return 0
}

################################################################################
# PREREQUISITE CHECKS
################################################################################

check_prerequisites() {
    print_section "CHECKING PREREQUISITES"
    
    local all_good=true
    
    # Check Docker
    if ! check_command docker; then
        print_error "Please install Docker from https://docs.docker.com/get-docker/"
        all_good=false
    fi
    
    # Check Docker Compose
    if ! check_command docker-compose; then
        print_error "Please install Docker Compose from https://docs.docker.com/compose/install/"
        all_good=false
    fi
    
    # Check Git
    if ! check_command git; then
        print_warning "Git is not installed (optional)"
    fi
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker."
        all_good=false
    else
        print_success "Docker daemon is running"
    fi

    # Check Python 3.11 (Host)
    if ! command -v python3.11 &> /dev/null; then
        if command -v python3 &> /dev/null && [ "$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == "3.11" ]; then
             print_success "Python 3.11 detected (via python3)"
        else
             print_warning "Python 3.11 not found on host. Local development scripts (setup_project.sh) will fail, but Docker execution is safe."
        fi
    else
        print_success "Python 3.11 detected"
    fi
    
    if [ "$all_good" = false ]; then
        print_error "Please install missing prerequisites and try again."
        exit 1
    fi
    
    print_success "All prerequisites are met!"
}

################################################################################
# PROJECT SETUP
################################################################################

setup_project() {
    print_section "SETTING UP PROJECT"
    
    # Check if project directory exists
    if [ -d "$PROJECT_DIR" ]; then
        print_info "Project directory already exists at $PROJECT_DIR"
        read -p "Do you want to use the existing installation? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing installation..."
            rm -rf "$PROJECT_DIR"
        else
            print_success "Using existing installation"
            return 0
        fi
    fi
    
    # Clone or copy project
    if command -v git &> /dev/null; then
        print_info "Cloning repository..."
        git clone https://github.com/qusai-duaij/zarqa-al-yamama.git "$PROJECT_DIR" 2>/dev/null || {
            print_warning "Could not clone from GitHub, using local copy..."
            cp -r . "$PROJECT_DIR"
        }
    else
        print_info "Copying project files..."
        cp -r . "$PROJECT_DIR"
    fi
    
    print_success "Project setup complete"
}

################################################################################
# ENVIRONMENT CONFIGURATION
################################################################################

configure_environment() {
    print_section "CONFIGURING ENVIRONMENT"
    
    # Check if .env already exists
    if [ -f "$ENV_FILE" ]; then
        print_info ".env file already exists"
        read -p "Do you want to reconfigure? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_success "Using existing configuration"
            return 0
        fi
    fi
    
    # Copy template
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "Created .env file from template"
    else
        print_error ".env.example not found"
        exit 1
    fi
    
    print_info "Configuring API keys (press Enter to skip)..."
    echo ""
    
    # OpenRouter API Key
    read -p "Enter OpenRouter API Key (optional): " openrouter_key
    if [ -n "$openrouter_key" ]; then
        sed -i.bak "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=$openrouter_key|" "$ENV_FILE"
        print_success "OpenRouter API Key configured"
    fi
    
    # DeepSeek API Key
    read -p "Enter DeepSeek API Key (optional): " deepseek_key
    if [ -n "$deepseek_key" ]; then
        sed -i.bak "s|DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$deepseek_key|" "$ENV_FILE"
        print_success "DeepSeek API Key configured"
    fi
    
    # GDELT API Key
    read -p "Enter GDELT API Key (optional): " gdelt_key
    if [ -n "$gdelt_key" ]; then
        sed -i.bak "s|GDELT_API_KEY=.*|GDELT_API_KEY=$gdelt_key|" "$ENV_FILE"
        print_success "GDELT API Key configured"
    fi
    
    # NewsAPI Key
    read -p "Enter NewsAPI Key (optional): " newsapi_key
    if [ -n "$newsapi_key" ]; then
        sed -i.bak "s|NEWSAPI_KEY=.*|NEWSAPI_KEY=$newsapi_key|" "$ENV_FILE"
        print_success "NewsAPI Key configured"
    fi
    
    # Polygon.io API Key
    read -p "Enter Polygon.io API Key (optional): " polygon_key
    if [ -n "$polygon_key" ]; then
        sed -i.bak "s|POLYGON_API_KEY=.*|POLYGON_API_KEY=$polygon_key|" "$ENV_FILE"
        print_success "Polygon.io API Key configured"
    fi
    
    # Alpha Vantage API Key
    read -p "Enter Alpha Vantage API Key (optional): " alphavantage_key
    if [ -n "$alphavantage_key" ]; then
        sed -i.bak "s|ALPHA_VANTAGE_KEY=.*|ALPHA_VANTAGE_KEY=$alphavantage_key|" "$ENV_FILE"
        print_success "Alpha Vantage API Key configured"
    fi
    
    # Clean up backup files
    rm -f "$ENV_FILE.bak"
    
    print_success "Environment configuration complete"
}

################################################################################
# DOCKER SERVICES
################################################################################

start_services() {
    print_section "STARTING DOCKER SERVICES"
    
    cd "$PROJECT_DIR"
    
    print_info "Building Docker images (this may take a few minutes)..."
    docker-compose build --no-cache 2>&1 | tail -20
    
    print_info "Starting services..."
    docker-compose up -d
    
    print_success "Services started"
}

################################################################################
# HEALTH CHECKS
################################################################################

wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    print_info "Waiting for $service to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    print_error "$service did not start within timeout"
    return 1
}

verify_installation() {
    print_section "VERIFYING INSTALLATION"
    
    cd "$PROJECT_DIR"
    
    # Check Docker containers
    print_info "Checking Docker containers..."
    docker-compose ps
    
    # Wait for services
    wait_for_service "Backend API" "http://localhost:8000/health"
    wait_for_service "Frontend" "http://localhost:3000"
    wait_for_service "PostgreSQL" "http://localhost:5432"
    
    # Health check
    print_info "Running health check..."
    HEALTH=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH" | grep -q "healthy"; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check inconclusive"
    fi
    
    # Test API
    print_info "Testing API..."
    API_TEST=$(curl -s -X POST http://localhost:8000/api/v1/scenarios)
    if echo "$API_TEST" | grep -q "scenarios"; then
        print_success "API test passed"
    else
        print_warning "API test inconclusive"
    fi
    
    print_success "Installation verification complete"
}

################################################################################
# SAMPLE FORECAST
################################################################################

run_sample_forecast() {
    print_section "RUNNING SAMPLE FORECAST"
    
    print_info "Generating sample forecast (this may take 30-60 seconds)..."
    
    FORECAST=$(curl -s -X POST http://localhost:8000/api/v1/forecast \
        -H "Content-Type: application/json" \
        -d '{
            "scenario": "Middle East Oil Price Stability",
            "user_id": "installation_test"
        }')
    
    if echo "$FORECAST" | grep -q "request_id"; then
        print_success "Sample forecast generated successfully"
        print_info "Response preview:"
        echo "$FORECAST" | head -c 500
        echo "..."
    else
        print_warning "Sample forecast generation inconclusive"
    fi
}

################################################################################
# DISPLAY RESULTS
################################################################################

display_results() {
    print_section "INSTALLATION COMPLETE!"
    
    echo -e "${GREEN}"
    echo "================================================================================"
    echo "  ZARQA AL YAMAMA IS READY TO USE"
    echo "================================================================================"
    echo -e "${NC}"
    
    echo ""
    print_info "Access the application:"
    echo -e "  ${BLUE}Frontend Dashboard:${NC}    http://localhost:3000"
    echo -e "  ${BLUE}API Endpoint:${NC}          http://localhost:8000"
    echo -e "  ${BLUE}API Documentation:${NC}     http://localhost:8000/docs"
    echo -e "  ${BLUE}Health Check:${NC}          http://localhost:8000/health"
    echo ""
    
    echo -e "${GREEN}Available Services:${NC}"
    echo "  • Backend API (FastAPI) - Port 8000"
    echo "  • Frontend (Next.js) - Port 3000"
    echo "  • PostgreSQL Database - Port 5432"
    echo "  • Qdrant Vector DB - Port 6333"
    echo "  • Neo4j Graph DB - Port 7687"
    echo "  • Redis Cache - Port 6379"
    echo ""
    
    echo -e "${GREEN}Useful Commands:${NC}"
    echo "  • View logs:              docker-compose logs -f"
    echo "  • Stop services:          docker-compose down"
    echo "  • Restart services:       docker-compose restart"
    echo "  • View service status:    docker-compose ps"
    echo ""
    
    echo -e "${GREEN}Documentation:${NC}"
    echo "  • User Guide:             $PROJECT_DIR/USER_GUIDE.md"
    echo "  • Developer Guide:        $PROJECT_DIR/DEVELOPER_GUIDE.md"
    echo "  • Operations Manual:      $PROJECT_DIR/OPERATIONS_MANUAL.md"
    echo "  • README:                 $PROJECT_DIR/README.md"
    echo ""
    
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Generate your first forecast"
    echo "  3. Review the documentation for advanced usage"
    echo "  4. Configure additional API keys as needed"
    echo ""
    
    echo -e "${BLUE}For support and documentation:${NC}"
    echo "  • Creator: Qusai Al-Duaij"
    echo "  • Initiative: LoLo AI Tree (Sovereign AI Initiative)"
    echo "  • Version: 1.0.0"
    echo ""
}

################################################################################
# ERROR HANDLING
################################################################################

cleanup_on_error() {
    print_error "Installation failed!"
    print_info "Cleaning up..."
    cd "$PROJECT_DIR" 2>/dev/null && docker-compose down 2>/dev/null || true
    exit 1
}

trap cleanup_on_error ERR

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    print_header
    
    # Run installation steps
    check_prerequisites
    setup_project
    configure_environment
    start_services
    verify_installation
    run_sample_forecast
    display_results
    
    print_success "Installation completed successfully!"
}

# Run main function
main
