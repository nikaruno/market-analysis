#!/bin/bash
################################################################################
# RUN ANALYSIS (without GUI)
################################################################################

# Set Python path
export PYTHONPATH="$(pwd)/src/exMarket:$(pwd):$PYTHONPATH"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        Running Market Analysis                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This will take 15-20 minutes..."
echo ""

python3 automation_scripts/automate_analysis_with_tech.py

echo ""
echo "✓ Analysis complete!"
echo ""
echo "View report:"
echo "  cat data/executive_summary.md"
echo ""
