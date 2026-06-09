# Part 1: Handler + Start Script

## Task 1: RunPod Handler (`handler.py`)

**Files:**
- Create: `handler.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```txt
runpod>=1.7.0
requests>=2.31.0
Pillow>=10.0.0
```

- [ ] **Step 2: Write handler.py**

```python
import os
import json
import time
import uuid
import base64
import requests
import runpod

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_DIR = "/app/workflows"
COMFYUI_INPUT_DIR = "/app/ComfyUI/input"
COMFYUI_OUTPUT_DIR = "/app/ComfyUI/output"
POLL_INTERVAL = 0.5
MAX_POLL_TIME = 300


def wait_for_comfyui(timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
            if r.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False


def load_workflow(workflow_name="default_workflow.json"):
    path = os.path.join(WORKFLOW_DIR, workflow_name)
    with open(path, "r") as f:
        return json.load(f)


def save_input_image(image_base64):
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(COMFYUI_INPUT_DIR, filename)
    image_data = base64.b64decode(image_base64)
    with open(filepath, "wb") as f:
        f.write(image_data)
    return filename


def inject_params(workflow, prompt_text, image_filename=None, params=None):
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")

        if "inputs" in node:
            inputs = node["inputs"]

            if "text" in inputs and "prompt" in class_type.lower():
                inputs["text"] = prompt_text

            if "seed" in inputs and params and "seed" in params:
                inputs["seed"] = params["seed"]

            if "steps" in inputs and params and "steps" in params:
                inputs["steps"] = params["steps"]

            if "cfg" in inputs and params and "cfg_scale" in params:
                inputs["cfg"] = params["cfg_scale"]

            if "width" in inputs and params and "width" in params:
                inputs["width"] = params["width"]

            if "height" in inputs and params and "height" in params:
                inputs["height"] = params["height"]

            if image_filename and "image" in inputs and "load" in class_type.lower():
                inputs["image"] = image_filename

    return workflow


def get_output_images(prompt_id):
    deadline = time.time() + MAX_POLL_TIME
    while time.time() < deadline:
        r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
        if r.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue

        history = r.json()
        if prompt_id not in history:
            time.sleep(POLL_INTERVAL)
            continue

        entry = history[prompt_id]
        if entry.get("status", {}).get("completed", False) is False:
            status_msg = entry.get("status", {}).get("status_str", "")
            if "error" in status_msg.lower():
                raise RuntimeError(f"ComfyUI execution error: {status_msg}")
            time.sleep(POLL_INTERVAL)
            continue

        outputs = entry.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                images = node_output["images"]
                if images:
                    img_info = images[0]
                    img_path = os.path.join(
                        COMFYUI_OUTPUT_DIR, img_info["subfolder"], img_info["filename"]
                    ) if img_info.get("subfolder") else os.path.join(
                        COMFYUI_OUTPUT_DIR, img_info["filename"]
                    )
                    with open(img_path, "rb") as f:
                        return base64.b64encode(f.read()).decode("utf-8")

        raise RuntimeError("No output images found in ComfyUI response")

    raise TimeoutError(f"ComfyUI did not complete within {MAX_POLL_TIME}s")


def handler(job):
    job_input = job["input"]

    prompt_text = job_input.get("prompt")
    if not prompt_text:
        return {"error": "Missing required field: prompt"}

    image_base64 = job_input.get("image")
    workflow_params = job_input.get("workflow_params", {})
    workflow_name = job_input.get("workflow", "default_workflow.json")

    try:
        workflow = load_workflow(workflow_name)
    except FileNotFoundError:
        return {"error": f"Workflow not found: {workflow_name}"}

    image_filename = None
    if image_base64:
        image_filename = save_input_image(image_base64)

    seed = workflow_params.get("seed", int.from_bytes(os.urandom(4), "big"))
    workflow_params.setdefault("seed", seed)

    workflow = inject_params(workflow, prompt_text, image_filename, workflow_params)

    payload = {"prompt": workflow}
    r = requests.post(f"{COMFYUI_URL}/prompt", json=payload, timeout=10)

    if r.status_code != 200:
        return {"error": f"ComfyUI rejected prompt: {r.text}"}

    prompt_id = r.json().get("prompt_id")
    if not prompt_id:
        return {"error": "No prompt_id returned from ComfyUI"}

    try:
        output_image = get_output_images(prompt_id)
    except (RuntimeError, TimeoutError) as e:
        return {"error": str(e)}

    return {"output": {"image": output_image, "seed": seed}}


if __name__ == "__main__":
    if not wait_for_comfyui():
        print("ERROR: ComfyUI failed to start")
        exit(1)
    print("ComfyUI is ready, starting RunPod handler...")
    runpod.serverless.start({"handler": handler})
```

- [ ] **Step 3: Test locally (dry run)**

Run: `python -c "import handler; print('imports OK')"`

This verifies the module imports cleanly. Full integration testing requires ComfyUI running.

- [ ] **Step 4: Commit**

```bash
git add handler.py requirements.txt
git commit -m "feat: add RunPod serverless handler for ComfyUI"
```

---

## Task 2: Start Script (`start.sh`)

**Files:**
- Create: `start.sh`

- [ ] **Step 1: Write start.sh**

```bash
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
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x start.sh
git add start.sh
git commit -m "feat: add start script for ComfyUI + handler"
```
