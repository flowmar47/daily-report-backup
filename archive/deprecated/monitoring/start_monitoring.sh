#!/bin/bash

# OhmsAlertsReports Monitoring Dashboard Startup Script
# This script sets up and starts the monitoring dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ohms/OhmsAlertsReports/daily-report"
MONITORING_DIR="$PROJECT_DIR/monitoring"
VENV_DIR="$PROJECT_DIR/venv"
DASHBOARD_PORT=5000
LOG_FILE="$PROJECT_DIR/logs/monitoring.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    netstat -tuln 2>/dev/null | grep -q ":$1 "
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing monitoring dependencies..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        print_status "Please run the main setup script first"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install required packages
    pip install flask psutil requests schedule >/dev/null 2>&1 || {
        print_error "Failed to install Python dependencies"
        exit 1
    }
    
    print_success "Dependencies installed successfully"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$MONITORING_DIR/templates"
    
    print_success "Directories created"
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check if running as root (for systemctl commands)
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root - some features may not work properly"
    fi
    
    # Check if systemd is available
    if ! command_exists systemctl; then
        print_warning "systemctl not found - service monitoring will be limited"
    fi
    
    print_success "System requirements check passed"
}

# Function to check if monitoring is already running
check_running() {
    if pgrep -f "dashboard.py" >/dev/null; then
        print_warning "Monitoring dashboard is already running"
        read -p "Do you want to stop it and restart? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_monitoring
        else
            print_status "Exiting..."
            exit 0
        fi
    fi
}

# Function to stop monitoring
stop_monitoring() {
    print_status "Stopping monitoring dashboard..."
    
    pkill -f "dashboard.py" || true
    
    # Wait a moment for process to stop
    sleep 2
    
    if pgrep -f "dashboard.py" >/dev/null; then
        print_warning "Force killing monitoring processes..."
        pkill -9 -f "dashboard.py" || true
    fi
    
    print_success "Monitoring dashboard stopped"
}

# Function to start monitoring
start_monitoring() {
    print_status "Starting monitoring dashboard..."
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Check if port is available
    if port_in_use $DASHBOARD_PORT; then
        print_error "Port $DASHBOARD_PORT is already in use"
        print_status "Please stop the service using that port or change the dashboard port"
        exit 1
    fi
    
    # Start the dashboard in background
    nohup python "$MONITORING_DIR/dashboard.py" > "$LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    
    # Wait a moment for the dashboard to start
    sleep 3
    
    # Check if dashboard started successfully
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        print_success "Monitoring dashboard started successfully"
        print_status "Dashboard URL: http://localhost:$DASHBOARD_PORT"
        print_status "Log file: $LOG_FILE"
        print_status "PID: $DASHBOARD_PID"
        
        # Save PID to file for easy management
        echo $DASHBOARD_PID > "$MONITORING_DIR/dashboard.pid"
        
        # Show dashboard status
        sleep 2
        if curl -s http://localhost:$DASHBOARD_PORT >/dev/null 2>&1; then
            print_success "Dashboard is responding to requests"
        else
            print_warning "Dashboard may still be starting up..."
        fi
    else
        print_error "Failed to start monitoring dashboard"
        print_status "Check the log file: $LOG_FILE"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Checking monitoring dashboard status..."
    
    if [ -f "$MONITORING_DIR/dashboard.pid" ]; then
        PID=$(cat "$MONITORING_DIR/dashboard.pid")
        if kill -0 $PID 2>/dev/null; then
            print_success "Monitoring dashboard is running (PID: $PID)"
            
            # Check if dashboard is responding
            if curl -s http://localhost:$DASHBOARD_PORT >/dev/null 2>&1; then
                print_success "Dashboard is responding at http://localhost:$DASHBOARD_PORT"
            else
                print_warning "Dashboard is running but not responding to requests"
            fi
        else
            print_warning "Dashboard PID file exists but process is not running"
            rm -f "$MONITORING_DIR/dashboard.pid"
        fi
    else
        print_warning "No dashboard PID file found"
    fi
    
    # Show recent logs
    if [ -f "$LOG_FILE" ]; then
        print_status "Recent log entries:"
        tail -n 5 "$LOG_FILE" | sed 's/^/  /'
    fi
}

# Function to show help
show_help() {
    echo "OhmsAlertsReports Monitoring Dashboard"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the monitoring dashboard"
    echo "  stop      Stop the monitoring dashboard"
    echo "  restart   Restart the monitoring dashboard"
    echo "  status    Show dashboard status"
    echo "  install   Install dependencies"
    echo "  help      Show this help message"
    echo ""
    echo "The dashboard will be available at http://localhost:$DASHBOARD_PORT"
}

# Main script logic
main() {
    case "${1:-start}" in
        start)
            check_requirements
            create_directories
            install_dependencies
            check_running
            start_monitoring
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            stop_monitoring
            sleep 2
            check_requirements
            create_directories
            install_dependencies
            start_monitoring
            ;;
        status)
            show_status
            ;;
        install)
            check_requirements
            create_directories
            install_dependencies
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 