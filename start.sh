#!/bin/bash
set -e

echo "=== Environment ==="
echo "Network volume contents:"
ls -la /runpod-volume/ 2>&1 || echo "WARNING: /runpod-volume not mounted"
ls -la /runpod-volume/runpod-slim/ComfyUI/models/ 2>&1 || echo "WARNING: models dir not found"

echo ""
echo "=== Starting ComfyUI server ==="
cd /app/ComfyUI

python main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    --disable-auto-launch \
    --extra-model-paths-config /app/extra_model_paths.yaml \
    2>&1 | tee /tmp/comfyui.log &

COMFYUI_PID=$!

echo "ComfyUI PID: $COMFYUI_PID"
echo "Waiting for ComfyUI to be ready..."
TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
        echo "ComfyUI is ready (took ${ELAPSED}s)"
        break
    fi
    if ! kill -0 $COMFYUI_PID 2>/dev/null; then
        echo "ERROR: ComfyUI process died"
        echo "=== ComfyUI logs ==="
        cat /tmp/comfyui.log
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "ERROR: ComfyUI failed to start within ${TIMEOUT}s"
    echo "=== ComfyUI logs ==="
    cat /tmp/comfyui.log
    kill $COMFYUI_PID 2>/dev/null
    exit 1
fi

echo "=== Starting RunPod handler ==="
cd /app
python -u handler.py
