"""Test script for Anima image generation API on RunPod Serverless."""

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

PAYLOAD = {
    "input": {
        "prompt": "masterpiece, best quality, 1girl, blonde hair, blue eyes, standing, looking at viewer",
        "workflow_params": {
            "negative_prompt": "score_1, score_2, score_3, blurry, worst quality, low quality",
            "steps": 30,
            "cfg": 4,
            "width": 832,
            "height": 1216,
        },
    }
}


def run_sync():
    """Submit job via /runsync (waits for result)."""
    print("Submitting job via /runsync ...")
    resp = requests.post(f"{BASE_URL}/runsync", headers=HEADERS, json=PAYLOAD, timeout=300)
    resp.raise_for_status()
    result = resp.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def run_async():
    """Submit job via /run (async) and poll for result."""
    print("Submitting job via /run ...")
    resp = requests.post(f"{BASE_URL}/run", headers=HEADERS, json=PAYLOAD, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    job_id = data.get("id")
    print(f"Job submitted: {job_id}")
    print(f"Status: {data.get('status')}")

    print("\nPolling for result...")
    while True:
        time.sleep(5)
        status_resp = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS, timeout=30)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data.get("status")
        print(f"  Status: {status}")

        if status == "COMPLETED":
            output = status_data.get("output", {})
            if "image" in output.get("output", {}):
                print(f"  Image received (base64 length: {len(output['output']['image'])})")
            else:
                print(json.dumps(output, indent=2, ensure_ascii=False))
            return status_data
        elif status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            print(f"  Job failed: {json.dumps(status_data, indent=2)}")
            return status_data


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "async"
    if mode == "sync":
        run_sync()
    else:
        run_async()
