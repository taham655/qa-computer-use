#!/bin/bash
set -e

./start_all.sh
./novnc_startup.sh

python http_server.py > /tmp/server_logs.txt 2>&1 &

# Check which app to run (default: original demo, qa: QA app)
APP_MODE=${APP_MODE:-demo}

if [ "$APP_MODE" = "qa" ]; then
    echo "🧪 Starting RoverQA (FastAPI + React)..."
    cd $HOME
    python -m uvicorn computer_use_demo.api:app --host 0.0.0.0 --port 8501 > /tmp/fastapi_stdout.log 2>&1 &
    echo "✨ RoverQA is ready!"
    echo "➡️  Open http://localhost:8501 in your browser for RoverQA"
    echo "➡️  Open http://localhost:6080/vnc.html to view the virtual desktop"
elif [ "$APP_MODE" = "qa-legacy" ]; then
    echo "🧪 Starting RoverQA (Streamlit - Legacy)..."
    STREAMLIT_SERVER_PORT=8501 python -m streamlit run computer_use_demo/qa_app.py > /tmp/streamlit_stdout.log 2>&1 &
    echo "✨ RoverQA (Legacy) is ready!"
    echo "➡️  Open http://localhost:8501 in your browser for RoverQA"
    echo "➡️  Open http://localhost:6080/vnc.html to view the virtual desktop"
else
    echo "🖥️  Starting Computer Use Demo..."
    STREAMLIT_SERVER_PORT=8501 python -m streamlit run computer_use_demo/streamlit.py > /tmp/streamlit_stdout.log 2>&1 &
    echo "✨ Computer Use Demo is ready!"
    echo "➡️  Open http://localhost:8080 in your browser to begin"
fi

# Keep the container running
tail -f /dev/null
