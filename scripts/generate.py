"""Generate images via Anima API on RunPod Serverless."""

import base64
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RUNPOD_API_KEY")
ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

if not API_KEY:
    sys.exit("Error: RUNPOD_API_KEY not set in .env")
if not ENDPOINT_ID:
    sys.exit("Error: RUNPOD_ENDPOINT_ID not set in .env")

BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


def save_image(image_base64):
    """Save base64 image to output directory, return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = int(time.time())
    filename = f"anima_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_base64))
    return filepath


def build_payload(prompt, negative_prompt=None, steps=30, cfg=4, width=832, height=1216, seed=None):
    payload = {
        "input": {
            "prompt": prompt,
            "workflow_params": {
                "negative_prompt": negative_prompt or "score_1, score_2, score_3, blurry, worst quality, low quality",
                "steps": steps,
                "cfg": cfg,
                "width": width,
                "height": height,
            },
        }
    }
    if seed is not None:
        payload["input"]["workflow_params"]["seed"] = seed
    return payload


def extract_image(result):
    """Extract base64 image from API result."""
    output = result.get("output", {})
    if isinstance(output, dict) and "image" in output:
        return output["image"]
    if isinstance(output, dict) and "output" in output:
        inner = output["output"]
        if isinstance(inner, dict) and "image" in inner:
            return inner["image"]
    return None


def generate(prompt, mode="async", **kwargs):
    """Submit a generation job and save the result."""
    payload = build_payload(prompt, **kwargs)

    if mode == "sync":
        print("Submitting job via /runsync ...")
        resp = requests.post(f"{BASE_URL}/runsync", headers=HEADERS, json=payload, timeout=300)
        resp.raise_for_status()
        result = resp.json()
    else:
        print("Submitting job via /run ...")
        resp = requests.post(f"{BASE_URL}/run", headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("id")
        print(f"Job submitted: {job_id}")
        print(f"Status: {data.get('status')}")

        print("Polling for result...")
        while True:
            time.sleep(5)
            status_resp = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS, timeout=30)
            status_resp.raise_for_status()
            result = status_resp.json()
            status = result.get("status")
            print(f"  Status: {status}")

            if status == "COMPLETED":
                break
            elif status in ("FAILED", "CANCELLED", "TIMED_OUT"):
                print(f"Job failed:\n{json.dumps(result, indent=2)}")
                return None

    image_b64 = extract_image(result)
    if image_b64:
        filepath = save_image(image_b64)
        print(f"Image saved: {filepath}")
        return filepath
    else:
        print(f"No image in response:\n{json.dumps(result, indent=2)}")
        return None


if __name__ == "__main__":
    mode = "async"
    args = sys.argv[1:]

    if "--sync" in args:
        mode = "sync"
        args.remove("--sync")

    prompt = " ".join(args) if args else "masterpiece, best quality, 1girl, blonde hair, blue eyes, standing, looking at viewer"
    generate(prompt, mode=mode)
