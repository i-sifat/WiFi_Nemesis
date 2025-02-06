#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo -e "${GREEN}"
    echo "██╗    ██╗██╗███████╗██╗    ███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗"
    echo "██║    ██║██║██╔════╝██║    ████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝"
    echo "██║ █╗ ██║██║█████╗  ██║    ██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗"
    echo "██║███╗██║██║██╔══╝  ██║    ██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║"
    echo "╚███╔███╔╝██║██║     ██║    ██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║"
    echo " ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝"
    echo -e "${NC}"
    echo -e "${CYAN}WiFi Nemesis Installer${NC}"
    echo -e "${CYAN}Version: 3.0.0${NC}"
    echo "----------------------------------------------------------------"
}

# Error handling
error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Success messages
success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Info messages
info() {
    echo -e "${CYAN}[INFO] $1${NC}"
}

# Warning messages
warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running with root
check_root() {
    if [ "$(id -u)" != "0" ]; then
        error "This installer needs root access. Please run with sudo."
        exit 1
    fi
}

# Check Termux environment
check_termux() {
    if [ -z "$(command -v termux-setup-storage)" ]; then
        error "This tool only supports Termux environment"
        exit 1
    fi
}

# Check Android version
check_android_version() {
    local version=$(getprop ro.build.version.release)
    if [ -z "$version" ] || [ "${version%%.*}" -lt 7 ]; then
        error "Android 7.0 or higher is required. Detected version: $version"
        exit 1
    fi
}

# Install required packages
install_packages() {
    info "Updating package lists..."
    pkg update -y || error "Failed to update package lists"
    
    info "Installing required packages..."
    pkg install -y \
        python \
        wpa-supplicant \
        pixiewps \
        iw \
        root-repo \
        tsu \
        git \
        openssl \
        || error "Failed to install required packages"
}

# Install Python dependencies
install_python_deps() {
    info "Installing Python dependencies..."
    pip install --upgrade pip || error "Failed to upgrade pip"
    pip install colorama || error "Failed to install Python dependencies"
}

# Setup WiFi Nemesis
setup_wifi_nemesis() {
    local install_dir="$HOME/wifi-nemesis"
    
    info "Cloning WiFi Nemesis repository..."
    rm -rf "$install_dir" 2>/dev/null
    git clone --depth 1 https://github.com/i-sifat/wifi-nemesis "$install_dir" || \
        error "Failed to clone repository"
    
    # Set permissions
    chmod +x "$install_dir/nemesis.py"
    
    # Create alias
    info "Creating command alias..."
    # Avoid duplicate aliases
    sed -i '/alias wa=/d' "$HOME/.bashrc" 2>/dev/null
    sed -i '/alias wa=/d' "$HOME/.zshrc" 2>/dev/null
    echo "alias wa='sudo python $install_dir/nemesis.py'" >> "$HOME/.bashrc"
    echo "alias wa='sudo python $install_dir/nemesis.py'" >> "$HOME/.zshrc"
    
    # Create a direct executable link
    mkdir -p "$HOME/.local/bin"
    ln -sf "$install_dir/nemesis.py" "$HOME/.local/bin/wa"
    chmod +x "$HOME/.local/bin/wa"
    
    # Add local bin to PATH if not already present
    if ! grep -q '$HOME/.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    if ! grep -q '$HOME/.local/bin' "$HOME/.zshrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
}

# Verify installation
verify_installation() {
    info "Verifying installation..."
    
    # Check required commands
    local commands=("python" "wpa_supplicant" "pixiewps" "iw")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Verify nemesis.py exists and is executable
    if [ ! -x "$HOME/wifi-nemesis/nemesis.py" ]; then
        error "nemesis.py not found or not executable"
        exit 1
    fi
    
    success "Installation verified successfully"
}

# Main installation process
main() {
    print_banner
    
    # Environment checks
    info "Performing environment checks..."
    check_termux
    check_android_version
    
    # Installation steps
    install_packages
    install_python_deps
    setup_wifi_nemesis
    verify_installation
    
    # Final instructions
    echo
    success "WiFi Nemesis has been installed successfully!"
    echo
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  ${GREEN}wa${NC} - Launch WiFi Nemesis"
    echo
    echo -e "${YELLOW}Note: Please restart Termux or run 'source ~/.bashrc' to use the 'wa' command${NC}"
    echo
    warning "This tool is for educational purposes only. Use responsibly and legally."
}

# Run main installation
main "$@"
