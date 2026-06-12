FROM nvidia/cuda:12.8.0-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI \
    && cd /app/ComfyUI \
    && pip install --no-cache-dir --break-system-packages -r requirements.txt

RUN pip install --no-cache-dir --break-system-packages torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

# Install custom nodes (add as needed)
# RUN cd /app/ComfyUI/custom_nodes \
#     && git clone https://github.com/<org>/<node>.git

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /app/requirements.txt

COPY handler.py /app/handler.py
COPY start.sh /app/start.sh
COPY extra_model_paths.yaml /app/extra_model_paths.yaml
COPY workflows/ /app/workflows/

RUN chmod +x /app/start.sh
RUN mkdir -p /app/ComfyUI/input /app/ComfyUI/output

CMD ["/app/start.sh"]
