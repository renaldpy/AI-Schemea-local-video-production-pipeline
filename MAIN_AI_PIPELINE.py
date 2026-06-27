import asyncio
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# ❌ REMOVE this (causes circular import if AI_App imports you)
# from AI_App import CorporateUIApp, Json_File_Parsing

# ✅ ONLY import UI class
from AI_App import CorporateUIApp

# ── Make sure sibling scripts are importable ────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
import Flux_Image_Gen
import WAN_I2V_Gen
# ───────────────────────────────────────────────────────────────────────

MAX_WORKERS = 4


# ─── Async wrappers ────────────────────────────────────────────────────

async def run_Flux_Image_Gen(scene_data, executor):
    loop = asyncio.get_running_loop()

    scene_number = scene_data["scene"]
    prompt = scene_data["prompt"]

    print(f"[MAIN] ▶ Scene {scene_number}")

    saved_paths = await loop.run_in_executor(
        executor,
        Flux_Image_Gen.run,
        prompt,
        scene_number
    )

    return saved_paths


async def run_WAN_I2V_Gen(image_path, positive_prompt, negative_prompt, executor):
    loop = asyncio.get_running_loop()

    print(f"[MAIN] ▶ Video for: {image_path}")

    saved_paths = await loop.run_in_executor(
        executor,
        WAN_I2V_Gen.run,
        image_path,
        positive_prompt,
        negative_prompt
    )

    return saved_paths


# ─── MAIN PIPELINE (NOW TAKES SCENES FROM UI) ───────────────────────────

async def pipeline(scenes):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        # 🔥 IMAGE GENERATION
        image_tasks = [
            asyncio.create_task(run_Flux_Image_Gen(scene, executor))
            for scene in scenes
        ]

        image_results = await asyncio.gather(*image_tasks)

        # Flatten results
        image_paths = [p for result in image_results for p in result]

        print(f"[MAIN] ✔ Generated {len(image_paths)} image(s)")

        # # 🔥 VIDEO GENERATION (optional)
        # video_tasks = [
        #     asyncio.create_task(run_WAN_I2V_Gen(path, executor))
        #     for path in image_paths
        # ]

        # await asyncio.gather(*video_tasks)

        print("[MAIN] ✔ Pipeline complete")


# ─── CALLBACK FROM UI (IMPORTANT) ───────────────────────────────────────

def start_pipeline(app):
    print("[PIPELINE] Starting after UI load...")

    # ✅ GET SCENES DIRECTLY FROM UI
    scenes = app.prepare_scenes()

    # ✅ RUN ASYNC PIPELINE IN BACKGROUND THREAD
    threading.Thread(
        target=lambda: asyncio.run(pipeline(scenes)),
        daemon=True
    ).start()


# ─── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CorporateUIApp(on_ready_callback=start_pipeline)
    app.mainloop()