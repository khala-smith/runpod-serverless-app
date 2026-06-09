# Part 3: Workflow Template + README

## Task 5: Default Workflow Template

**Files:**
- Create: `workflows/default_workflow.json`

- [ ] **Step 1: Create workflows directory and placeholder workflow**

This is a minimal ComfyUI workflow structure. You should replace this with your actual QwenImageEdit workflow JSON exported from ComfyUI.

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "your_model.safetensors"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "placeholder prompt",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "",
      "clip": ["1", 1]
    }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 0,
      "steps": 20,
      "cfg": 7.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    }
  },
  "7": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "output",
      "images": ["6", 0]
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p workflows
# (save the JSON above as workflows/default_workflow.json)
git add workflows/default_workflow.json
git commit -m "feat: add placeholder workflow template"
```

---

## Task 6: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
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
      "cfg_scale": 7.5,
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```
