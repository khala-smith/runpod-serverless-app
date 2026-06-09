# ComfyUI Serverless Worker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy a ComfyUI-based image generation/editing worker on RunPod Serverless with models loaded from a network volume.

**Architecture:** ComfyUI runs in API mode inside the container. A RunPod handler submits workflow JSON to ComfyUI's local API, polls for completion, and returns base64-encoded output images. Models live on a network volume mounted at `/runpod-volume`.

**Tech Stack:** Python 3.11, RunPod SDK, ComfyUI, Docker (nvidia/cuda:12.4.0), bash

**Plan files:**
1. [Task 1-2: Core handler + start script](./2026-06-09-comfyui-worker-part1.md)
2. [Task 3-4: Docker + config files](./2026-06-09-comfyui-worker-part2.md)
3. [Task 5-6: Workflow template + README](./2026-06-09-comfyui-worker-part3.md)

---
