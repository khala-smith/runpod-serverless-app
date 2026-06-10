#!/bin/bash
set -e

echo "Starting ComfyUI server..."
cd /app/ComfyUI

python main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    --disable-auto-launch \
    --extra-model-paths-config /app/extra_model_paths.yaml \
    &

COMFYUI_PID=$!

echo "Waiting for ComfyUI to be ready..."
TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
        echo "ComfyUI is ready (took ${ELAPSED}s)"
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "ERROR: ComfyUI failed to start within ${TIMEOUT}s"
    kill $COMFYUI_PID 2>/dev/null
    exit 1
fi

echo "Starting RunPod handler..."
cd /app
python -u handler.py
