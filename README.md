# ComfyUI Serverless Worker (RunPod)

A RunPod Serverless endpoint that runs ComfyUI in API mode for image generation and editing.

## Prerequisites

- Docker
- RunPod account with a network volume
- Model weights downloaded to the network volume

## Network Volume Setup

Create a RunPod network volume and populate it:

```
/runpod-volume/
└── models/
    ├── checkpoints/   ← your .safetensors model files
    ├── clip/
    ├── vae/
    ├── loras/
    └── controlnet/
```

You can download models by launching a temporary pod with the volume attached and running:

```bash
huggingface-cli download <model-repo> --local-dir /runpod-volume/models/checkpoints/
```

## Build & Deploy

1. Build the Docker image:

```bash
docker build -t your-registry/comfyui-worker:latest .
docker push your-registry/comfyui-worker:latest
```

2. Create a Serverless endpoint in the RunPod console:
   - Image: `your-registry/comfyui-worker:latest`
   - GPU: RTX 5090 (or compatible)
   - Network Volume: attach your volume
   - Volume Mount Path: `/runpod-volume`

## Usage

### Text-to-Image

```json
{
  "input": {
    "prompt": "a beautiful sunset over mountains",
    "workflow_params": {
      "steps": 30,
      "cfg": 7.5,
      "width": 1024,
      "height": 1024
    }
  }
}
```

### Image Editing

```json
{
  "input": {
    "prompt": "change the sky to night time",
    "image": "<base64-encoded-png>",
    "workflow_params": {
      "steps": 20
    }
  }
}
```

### Response

```json
{
  "output": {
    "image": "<base64-encoded-png>",
    "seed": 123456789
  }
}
```

## Custom Workflows

Place your ComfyUI workflow JSON files in the `workflows/` directory. Specify which workflow to use via the `workflow` field in the request input:

```json
{
  "input": {
    "prompt": "...",
    "workflow": "my_custom_workflow.json"
  }
}
```

## Local Testing

```bash
pip install -r requirements.txt
python handler.py --test_input '{"input": {"prompt": "test"}}'
```

Note: Local testing requires ComfyUI running on port 8188.

## Custom Nodes

To add custom nodes (e.g., for QwenImageEdit), uncomment and edit the relevant section in the `Dockerfile`:

```dockerfile
RUN cd /app/ComfyUI/custom_nodes \
    && git clone https://github.com/<org>/<node-repo>.git \
    && cd <node-repo> \
    && pip install --no-cache-dir -r requirements.txt
```
