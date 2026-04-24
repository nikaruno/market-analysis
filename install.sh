#!/bin/bash
################################################################################
# INSTALL - One time setup
################################################################################

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        Market Analysis - Install                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! python3 --version > /dev/null 2>&1; then
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Install packages
echo "→ Installing Python packages..."
echo ""

pip3 install pandas numpy yfinance beautifulsoup4 requests matplotlib streamlit plotly python-dateutil lxml 2>&1 | grep -v "Requirement already satisfied" || \
pip3 install --user pandas numpy yfinance beautifulsoup4 requests matplotlib streamlit plotly python-dateutil lxml 2>&1 | grep -v "Requirement already satisfied" || \
pip3 install --break-system-packages pandas numpy yfinance beautifulsoup4 requests matplotlib streamlit plotly python-dateutil lxml 2>&1 | grep -v "Requirement already satisfied"

echo ""
echo "✓ Packages installed"
echo ""

# Create directories
echo "→ Creating data directories..."
mkdir -p data/plots
mkdir -p data/fundamentals/raw
mkdir -p data/technical_charts
mkdir -p logs
echo "✓ Directories created"
echo ""

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                          Install Complete! ✓                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "To start the GUI:"
echo "  bash run_gui.sh"
echo ""
echo "To run analysis without GUI:"
echo "  bash run_analysis.sh"
echo ""
