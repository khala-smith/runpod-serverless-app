"""RunPod serverless handler for ComfyUI image generation/editing."""

import base64
import json
import os
import time
import uuid

import requests
import runpod

# Constants
COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_DIR = "/app/workflows"
COMFYUI_INPUT_DIR = "/app/ComfyUI/input"
COMFYUI_OUTPUT_DIR = "/app/ComfyUI/output"
POLL_INTERVAL = 0.5
MAX_POLL_TIME = 300


def wait_for_comfyui(timeout=120):
    """Poll ComfyUI /system_stats until it returns a 200 response."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
            if response.status_code == 200:
                print("ComfyUI is ready.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"ComfyUI did not become ready within {timeout} seconds.")


def load_workflow(workflow_name):
    """Read a workflow JSON template from WORKFLOW_DIR."""
    workflow_path = os.path.join(WORKFLOW_DIR, workflow_name)
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"Workflow not found: {workflow_path}")
    with open(workflow_path, "r") as f:
        return json.load(f)


def save_input_image(image_base64):
    """Decode a base64 image and save it to COMFYUI_INPUT_DIR with a uuid filename."""
    os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)
    image_data = base64.b64decode(image_base64)
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(COMFYUI_INPUT_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_data)
    return filename


def inject_params(workflow, prompt_text, image_filename, params):
    """Inject parameters into workflow nodes by matching class_type and input fields."""
    params = params or {}
    negative_prompt = params.get("negative_prompt")

    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        class_type = node.get("class_type", "")

        # Inject positive prompt into the first CLIPTextEncode (node "11")
        if class_type == "CLIPTextEncode" and "text" in inputs:
            if node_id == "11" and prompt_text is not None:
                inputs["text"] = prompt_text
            elif node_id == "12" and negative_prompt is not None:
                inputs["text"] = negative_prompt

        # Inject image filename into image loader nodes
        if class_type in ("LoadImage", "LoadImageMask"):
            if "image" in inputs and image_filename is not None:
                inputs["image"] = image_filename

        # Inject sampler parameters (KSampler and KSamplerAdvanced)
        if "noise_seed" in inputs and "seed" in params:
            inputs["noise_seed"] = params["seed"]
        if "seed" in inputs and "seed" in params:
            inputs["seed"] = params["seed"]
        if "steps" in inputs and "steps" in params:
            inputs["steps"] = params["steps"]
        if "cfg" in inputs and "cfg" in params:
            inputs["cfg"] = params["cfg"]

        # Inject dimensions into EmptyLatentImage
        if class_type == "EmptyLatentImage":
            if "width" in inputs and "width" in params:
                inputs["width"] = params["width"]
            if "height" in inputs and "height" in params:
                inputs["height"] = params["height"]

    return workflow


def get_output_images(prompt_id):
    """Poll /history/{prompt_id} for completion and return output image as base64."""
    start_time = time.time()

    while time.time() - start_time < MAX_POLL_TIME:
        try:
            response = requests.get(
                f"{COMFYUI_URL}/history/{prompt_id}", timeout=10
            )
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            for image_info in node_output["images"]:
                                image_filename = image_info.get("filename")
                                subfolder = image_info.get("subfolder", "")
                                if subfolder:
                                    image_path = os.path.join(
                                        COMFYUI_OUTPUT_DIR, subfolder, image_filename
                                    )
                                else:
                                    image_path = os.path.join(
                                        COMFYUI_OUTPUT_DIR, image_filename
                                    )
                                if os.path.exists(image_path):
                                    with open(image_path, "rb") as f:
                                        image_base64 = base64.b64encode(
                                            f.read()
                                        ).decode("utf-8")
                                    return image_base64
                    # History exists but no images yet or status not complete
                    status = history[prompt_id].get("status", {})
                    if status.get("status_str") == "error":
                        messages = status.get("messages", [])
                        raise RuntimeError(
                            f"ComfyUI execution failed: {messages}"
                        )
        except requests.exceptions.RequestException:
            pass

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        f"Image generation timed out after {MAX_POLL_TIME} seconds."
    )


def handler(job):
    """Main handler function for RunPod serverless."""
    try:
        job_input = job.get("input", {})

        # Extract inputs
        prompt_text = job_input.get("prompt")
        if not prompt_text:
            return {"error": "Missing required field: prompt"}
        image_base64 = job_input.get("image")
        workflow_params = job_input.get("workflow_params", {})
        workflow_name = job_input.get("workflow", "anima_basic.json")

        # Load workflow template
        workflow = load_workflow(workflow_name)

        # Save input image if provided
        image_filename = None
        if image_base64:
            image_filename = save_input_image(image_base64)

        # Generate a seed if not provided
        seed = workflow_params.get("seed", int(time.time()) % (2**32))
        workflow_params["seed"] = seed

        # Inject parameters into workflow
        workflow = inject_params(workflow, prompt_text, image_filename, workflow_params)

        # Submit workflow to ComfyUI
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=30,
        )

        if response.status_code != 200:
            return {"error": f"ComfyUI rejected the prompt: {response.text}"}

        result = response.json()
        prompt_id = result.get("prompt_id")

        if not prompt_id:
            return {"error": "No prompt_id returned from ComfyUI."}

        # Poll for output
        output_image = get_output_images(prompt_id)

        return {"output": {"image": output_image, "seed": seed}}

    except FileNotFoundError as e:
        return {"error": str(e)}
    except TimeoutError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


runpod.serverless.start({"handler": handler})
