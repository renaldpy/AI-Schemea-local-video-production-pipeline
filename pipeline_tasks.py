import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import sys

# Ensure the directory is in sys.path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))

import Flux_Image_Gen
import WAN_I2V_Gen

async def run_Flux_Image_Gen(scene_data, executor):
    """
    Async wrapper for image generation.
    scene_data should be a dict with "scene" (number) and "prompt" (string).
    """
    loop = asyncio.get_running_loop()

    scene_number = scene_data["scene"]
    prompt = scene_data["prompt"]

    print(f"[PIPELINE-TASK] ▶ Scene {scene_number}: Generating Image...")

    saved_paths = await loop.run_in_executor(
        executor,
        Flux_Image_Gen.run,
        prompt,
        scene_number
    )

    return saved_paths


async def run_WAN_I2V_Gen(image_path: str, executor: ThreadPoolExecutor) -> list[str]:
    """
    Async wrapper for image-to-video generation.
    """
    loop = asyncio.get_running_loop()
    print(f"[PIPELINE-TASK] ▶ Starting video generation for: {image_path}")
    saved_paths = await loop.run_in_executor(executor, WAN_I2V_Gen.run, image_path)
    print(f"[PIPELINE-TASK] ✔ Video generation complete for: {image_path}")
    return saved_paths
