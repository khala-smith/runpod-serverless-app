# ComfyUI Serverless Worker on RunPod

## Overview

A RunPod Serverless GPU worker that runs ComfyUI in API mode with QwenImageEdit models. Supports text-to-image generation and image editing via ComfyUI workflow execution. Models are loaded from a RunPod network volume.

## Architecture

### Components

1. **RunPod Handler** (`handler.py`) — Receives job requests, injects parameters into the ComfyUI workflow JSON, submits to ComfyUI's API, polls for results, and returns the output image.

2. **ComfyUI Server** — Runs in API mode (headless, no UI). Started before the handler begins accepting jobs. Listens on `127.0.0.1:8188`.

3. **Start Script** (`start.sh`) — Launches ComfyUI, waits for it to be ready, then starts the RunPod handler.

4. **Dockerfile** — Builds an image with ComfyUI, required custom nodes, Python dependencies, and the handler code. Models are NOT baked in.

5. **Network Volume** — Mounted at `/runpod-volume`, contains model weights downloaded from Hugging Face.

### Request Flow

```
Client Request
    │
    ▼
RunPod Serverless Infrastructure
    │
    ▼
handler.py (runpod.serverless.start)
    │
    ├─ Parse input (prompt, image, workflow_params)
    ├─ Load workflow JSON template
    ├─ Inject parameters into workflow nodes
    ├─ POST to ComfyUI /prompt endpoint
    ├─ Poll /history/{prompt_id} for completion
    ├─ Retrieve output image from ComfyUI output dir
    └─ Return base64-encoded image (or error)
```

### Network Volume Layout

```
/runpod-volume/
├── models/
│   ├── checkpoints/      # Main model weights
│   ├── clip/             # CLIP models if needed
│   ├── vae/              # VAE weights if separate
│   └── ...               # Other model directories as needed
└── output/               # (optional) persistent output storage
```

ComfyUI will be configured with `extra_model_paths.yaml` to point at `/runpod-volume/models/`.

## API Contract

### Input Schema

```json
{
  "input": {
    "prompt": "string (required) — text prompt for generation or editing instruction",
    "image": "string (optional) — base64-encoded input image for editing mode. Omit for text-to-image.",
    "workflow_params": {
      "// optional overrides for workflow node values": "",
      "seed": "integer (optional) — random seed",
      "steps": "integer (optional) — number of sampling steps",
      "cfg_scale": "number (optional) — classifier-free guidance scale",
      "width": "integer (optional) — output width",
      "height": "integer (optional) — output height"
    }
  }
}
```

### Output Schema

```json
{
  "output": {
    "image": "string — base64-encoded PNG output image",
    "seed": "integer — seed used for generation"
  }
}
```

### Error Schema

```json
{
  "error": "string — error message describing what went wrong"
}
```

## Project Structure

```
runpod-serverless-app/
├── handler.py                  # RunPod serverless handler
├── start.sh                    # Entrypoint: starts ComfyUI then handler
├── Dockerfile                  # Build image with ComfyUI + deps
├── extra_model_paths.yaml      # Points ComfyUI at network volume models
├── requirements.txt            # Python deps (runpod)
├── workflows/
│   └── default_workflow.json   # Default ComfyUI workflow template
└── README.md                   # Setup and deployment instructions
```

## Dockerfile Strategy

- **Base image:** `nvidia/cuda:12.4.0-runtime-ubuntu22.04` (compatible with RTX 5090)
- **Install:** Python 3.11, git, ComfyUI (cloned from GitHub), custom nodes for QwenImageEdit
- **Copy:** handler.py, start.sh, extra_model_paths.yaml, workflows/
- **Entrypoint:** `start.sh`
- Models are NOT included — they live on the network volume

## Handler Logic

1. **Startup:** ComfyUI starts via `start.sh`. Handler waits for ComfyUI to respond on port 8188 before calling `runpod.serverless.start()`.

2. **Job processing:**
   - Validate input (prompt is required)
   - If `image` is provided: decode base64, save to ComfyUI input dir, set image editing mode in workflow
   - If `image` is absent: configure workflow for text-to-image mode
   - Apply any `workflow_params` overrides to relevant nodes
   - Submit workflow to ComfyUI `/prompt` API
   - Poll `/history/{prompt_id}` until complete (with timeout)
   - Read output image, encode as base64, return

3. **Error handling:**
   - ComfyUI not ready → return error
   - Invalid input → return error with details
   - ComfyUI execution failure → return error from ComfyUI
   - Timeout → return timeout error

## GPU Target

- **Primary:** RTX 5090 (32GB VRAM)
- CUDA 12.4+ required for RTX 5090 support

## Deployment Steps

1. Create a RunPod network volume
2. Download QwenImageEdit model weights to the volume (via a temporary pod or download script)
3. Build and push the Docker image to Docker Hub or RunPod registry
4. Create a serverless endpoint pointing to the image, with the network volume attached
5. Test with a sample request

## Testing

- Local testing with `runpod` SDK's local test mode (`python handler.py --test_input`)
- Test both modes: text-to-image (no image input) and image editing (with image input)
- Verify ComfyUI startup and health check
- Verify timeout behavior for long-running workflows

## Constraints

- Cold start time depends on model loading from network volume (can be 30-60s for large models)
- ComfyUI must fully initialize before accepting jobs
- Output images are returned as base64 in the response body; for very large outputs, consider adding optional S3 upload
