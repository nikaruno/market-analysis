#!/bin/bash
################################################################################
# RUN GUI
################################################################################

# Set Python path
export PYTHONPATH="$(pwd)/src/exMarket:$(pwd):$PYTHONPATH"

# Add user bin to PATH
export PATH="$HOME/.local/bin:$PATH"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        Starting Market Analysis GUI                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Opening at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run streamlit (try different methods)
if command -v streamlit &> /dev/null; then
    streamlit run gui/app.py --server.port=8501 --server.address=localhost
elif [ -f "$HOME/.local/bin/streamlit" ]; then
    $HOME/.local/bin/streamlit run gui/app.py --server.port=8501 --server.address=localhost
else
    python3 -m streamlit run gui/app.py --server.port=8501 --server.address=localhost
fi
