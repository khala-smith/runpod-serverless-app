# Part 2: Docker + Config Files

## Task 3: Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI \
    && cd /app/ComfyUI \
    && pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

# Install custom nodes for QwenImageEdit
# Uncomment and modify the lines below for your specific custom nodes:
# RUN cd /app/ComfyUI/custom_nodes \
#     && git clone https://github.com/<org>/<qwen-image-edit-node>.git \
#     && cd <qwen-image-edit-node> \
#     && pip install --no-cache-dir -r requirements.txt

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY handler.py /app/handler.py
COPY start.sh /app/start.sh
COPY extra_model_paths.yaml /app/extra_model_paths.yaml
COPY workflows/ /app/workflows/

RUN chmod +x /app/start.sh
RUN mkdir -p /app/ComfyUI/input /app/ComfyUI/output

CMD ["/app/start.sh"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile with ComfyUI and CUDA 12.4"
```

---

## Task 4: Extra Model Paths Config (`extra_model_paths.yaml`)

**Files:**
- Create: `extra_model_paths.yaml`

- [ ] **Step 1: Write extra_model_paths.yaml**

```yaml
runpod_volume:
    base_path: /runpod-volume/models/
    checkpoints: checkpoints/
    clip: clip/
    vae: vae/
    loras: loras/
    controlnet: controlnet/
    upscale_models: upscale_models/
```

- [ ] **Step 2: Commit**

```bash
git add extra_model_paths.yaml
git commit -m "feat: add extra model paths config for network volume"
```
