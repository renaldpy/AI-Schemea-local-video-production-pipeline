# Developer Documentation

This document is intended for contributors and developers who want to understand the codebase internals, extend the pipeline, or integrate new generation backends.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Reference](#module-reference)
3. [Execution Order](#execution-order)
4. [Data Flow](#data-flow)
5. [ComfyUI API Protocol](#comfyui-api-protocol)
6. [JSON Pipeline](#json-pipeline)
7. [Extension Points](#extension-points)
8. [Code Quality Notes](#code-quality-notes)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        MAIN_AI_PIPELINE.py                         │
│  Entry point. Instantiates CorporateUIApp with a callback.         │
│  Callback fires after the user submits JSON in the UI.             │
└───────────────────────────────┬────────────────────────────────────┘
                                │ on_ready_callback(app)
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                           AI_App.py                                │
│  CorporateUIApp (Tkinter)                                          │
│  ├── show_input_page()          JSON entry screen                  │
│  ├── load_main_page()           Parses JSON → processed_output.json│
│  ├── setup_main_page()          Dashboard + Image Sequence pages    │
│  ├── Image_pipeline()           Async image gen coordinator        │
│  └── Video_pipeline()           Async video gen coordinator        │
│                                                                    │
│  process_scenes(json_input)     Parses raw JSON → 7 data streams   │
│  Json_File_Parsing()            Reads processed_output.json        │
└────┬──────────────────────┬─────────────────────────────────────┬──┘
     │                      │                                     │
     ▼                      ▼                                     ▼
┌──────────────┐  ┌──────────────────┐                ┌──────────────────────────┐
│Flux_Image_   │  │WAN_I2V_Gen.py    │                │Image_Sequence_Scenes.py  │
│Gen.py        │  │                  │                │                          │
│              │  │ run(image_path,  │                │ Image_sequence_generation│
│ run(prompt,  │  │   pos_prompt,    │                │   (scene_durations)      │
│  scene_num)  │  │   neg_prompt)    │                │                          │
│              │  │                  │                │ video_sequence_gen(id,   │
│ → IMAGE/*.png│  │ → VIDEO/*.mp4    │                │   duration, ratio)       │
└──────┬───────┘  └──────┬───────────┘                └──────────────────────────┘
       │                 │                                          │
       └────────┬────────┘               reads:  historical_selections.json
                ▼                        writes: VIDEO/{scene_id}_sequence.mp4
     ┌────────────────────┐
     │   ComfyUI          │
     │   127.0.0.1:8188   │
     │   WebSocket API    │
     └────────────────────┘


Separate standalone:
┌───────────────────────────────┐
│ Qwen_TTS.py                   │
│ run() → VOICE/*.flac          │
│ via ComfyUI Qwen3-TTS node    │
└───────────────────────────────┘
```

---

## Module Reference

### `MAIN_AI_PIPELINE.py`

**Role**: Application entry point.

**Key functions**:

| Function | Description |
|---|---|
| `run_Flux_Image_Gen(scene_data, executor)` | Async wrapper: calls `Flux_Image_Gen.run` in a thread pool |
| `run_WAN_I2V_Gen(image_path, pos, neg, executor)` | Async wrapper: calls `WAN_I2V_Gen.run` in a thread pool |
| `pipeline(scenes)` | Async pipeline: gathers image tasks; video section is commented out |
| `start_pipeline(app)` | Callback invoked by UI after JSON is loaded; extracts scenes from `app.prepare_scenes()` and runs `pipeline()` in a daemon thread |

**Entry point behaviour**:
```python
if __name__ == "__main__":
    app = CorporateUIApp(on_ready_callback=start_pipeline)
    app.mainloop()
```

---

### `AI_App.py`

**Role**: Main UI, JSON parser, and pipeline orchestrator.

**Important constants**:
```python
BASE_DIR   = r"D:\AI_Schemea"          # Must be updated per installation
IMAGE_DIR  = os.path.join(BASE_DIR, "IMAGE")
JSON_FILE  = os.path.join(BASE_DIR, "Text_Files", "processed_output.json")
MAX_WORKERS = 4
```

**Key functions**:

| Function | Description |
|---|---|
| `process_scenes(json_input)` | Parses raw LLM JSON array into 7 structured lists. Handles the three visual modes (AI-gen / reference download / historical photo). |
| `Json_File_Parsing()` | Reads `processed_output.json` and returns only scenes that have both a visual prompt and an animation (used for building the image-gen task list). |
| `CorporateUIApp.__init__()` | Initialises Tkinter, styles, and shows the input page. |
| `CorporateUIApp.prepare_scenes()` | Called by the pipeline callback; returns `[{scene, prompt}]` from the in-memory `self.prompts` dict. |
| `CorporateUIApp.load_main_page()` | Validates JSON, calls `process_scenes()`, writes JSON file, transitions to dashboard, fires callback. |
| `CorporateUIApp.load_data()` | Scans `IMAGE_DIR` for PNGs, groups by `scene{N}` prefix, reads prompts from JSON. |
| `CorporateUIApp.display_current_scene()` | Renders image grid cards for the current scene with Keep/Regen buttons. |
| `CorporateUIApp.keep_one_delete_rest()` | Deletes all images in a scene batch except the selected one. |
| `CorporateUIApp.regenerate_image()` | Re-runs `Image_pipeline()` for a single scene using the current prompt text. |
| `CorporateUIApp.video_process()` | Collects all scenes with non-null animations, builds video job list, runs `Video_pipeline()`. |
| `CorporateUIApp.finish_seq_selection()` | Saves `seq_selections` and `seq_aspect_ratios` to `historical_selections.json`. |
| `CorporateUIApp.trigger_image_sequence_generation()` | Collects durations + aspect ratios for all historical scenes, runs `Image_sequence_generation()` in a daemon thread. |
| `Image_pipeline(scenes)` | Async function: gathers `run_Flux_Image_Gen` tasks for a list of scenes. |
| `Video_pipeline(video_jobs)` | Async function: gathers `run_WAN_I2V_Gen` tasks for a list of image+prompt job dicts. |

---

### `Flux_Image_Gen.py`

**Role**: Communicates with ComfyUI to generate images using Flux 2.

**Configuration**:
```python
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_FOLDER  = "D:/AI_Schemea/IMAGE"
```

**Workflow nodes** (embedded as `PROMPT_TEXT` JSON string):

| Node ID | Class | Purpose |
|---|---|---|
| `98:105` | `UnetLoaderGGUF` | Loads `flux-2-klein-4b-Q8_0.gguf` |
| `98:101` | `LoraLoaderModelOnly` | Loads `Charcoal_E5.safetensors` (LoRA) |
| `98:102` | `ComfySwitchNode` | Toggles LoRA on/off |
| `98:104` | `PrimitiveBoolean` | LoRA enable flag (`true`) |
| `98:38` | `CLIPLoader` | Loads `qwen_3_4b_fp4_flux2.safetensors` |
| `98:6` | `CLIPTextEncode` | Encodes positive prompt **(injection point)** |
| `98:26` | `FluxGuidance` | Guidance scale = 3 |
| `98:25` | `RandomNoise` | Fixed seed `500436027408101` |
| `98:47` | `EmptyFlux2LatentImage` | 1024×1024, batch_size=4 |
| `98:48` | `Flux2Scheduler` | Steps from switch node |
| `98:99/100` | `PrimitiveInt` | Steps: 22 (turbo) / 20 (normal) |
| `98:103` | `ComfySwitchNode` | Switches step count |
| `98:16` | `KSamplerSelect` | Euler sampler |
| `98:13` | `SamplerCustomAdvanced` | Core sampling node |
| `98:10` | `VAELoader` | Loads `flux2-vae.safetensors` |
| `98:8` | `VAEDecode` | Decodes latent to image |
| `9` | `SaveImage` | Saves to ComfyUI output folder |

**Prompt injection**:
```python
prompt["98:6"]["inputs"]["text"] = parament_ImgPrompt
```

**Output naming**:
```
IMAGE/scene{scene_number}_{index}.png
```
(Produces 4 images per call due to `batch_size=4`.)

**Key functions**:

| Function | Description |
|---|---|
| `queue_prompt(prompt, prompt_id, client_id)` | POSTs workflow to `/prompt` |
| `wait_for_completion(ws, prompt_id)` | Blocks on WebSocket until `executing` → `node: null` |
| `generate_image(ws, prompt, client_id)` | Orchestrates queue → wait → download |
| `save_image(output_image, folder, scene_number)` | Writes bytes to `scene{N}_{idx}.png` |
| `free_memory()` | POSTs to `/free` to unload models from VRAM |
| `run(parament_ImgPrompt, scene_number)` | **Public entry point** |

---

### `WAN_I2V_Gen.py`

**Role**: Communicates with ComfyUI to convert images to video clips using Wan 2.1 I2V.

**Configuration**:
```python
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_FOLDER  = "D:/AI_Schemea/VIDEO"
```

**Workflow nodes** (embedded as `PROMPT_TEXT`):

| Node ID | Class | Purpose |
|---|---|---|
| `58` | `UnetLoaderGGUF` | Loads `wan2.1-i2v-14b-480p-Q3_K_S.gguf` |
| `59` | `LoraLoaderModelOnly` | Loads LightX2V LoRA |
| `54` | `ModelSamplingSD3` | Applies shift=8 |
| `38` | `CLIPLoader` | Loads `umt5_xxl_fp8_e4m3fn_scaled.safetensors` |
| `49` | `CLIPVisionLoader` | Loads `clip_vision_h.safetensors` |
| `52` | `LoadImage` | Input image **(injection point)** |
| `51` | `CLIPVisionEncode` | Encodes input image |
| `6` | `CLIPTextEncode` | Positive prompt **(injection point)** |
| `7` | `CLIPTextEncode` | Negative prompt **(injection point)** |
| `50` | `WanImageToVideo` | 480×480, 49 frames, batch_size=1 |
| `3` | `KSampler` | Euler, 11 steps, cfg=5.4 |
| `39` | `VAELoader` | Loads `wan_2.1_vae.safetensors` |
| `8` | `VAEDecode` | Decodes latent |
| `55` | `CreateVideo` | 16 fps |
| `56` | `SaveVideo` | Saves MP4 (node ID used in output filename) |

**Prompt injection**:
```python
prompt["52"]["inputs"]["image"] = input_image_path
prompt["6"]["inputs"]["text"]   = positive_prompt
prompt["7"]["inputs"]["text"]   = negative_prompt
```

**Output naming**:
```
VIDEO/{scene_prefix}_node{node_id}_{index}.mp4
# e.g. scene11_node56_0.mp4
```

**Key functions**:

| Function | Description |
|---|---|
| `generate_video(ws, prompt, client_id)` | Queues, waits, downloads video bytes |
| `save_video(output_video, folder, input_image_path)` | Derives scene prefix from image filename |
| `run(input_image_path, positive_prompt, negative_prompt)` | **Public entry point** |

---

### `Image_Sequence_Scenes.py`

**Role**: Assembles historical photo sequences into polished video clips using MoviePy and Pillow.

**Important caveat**: The file reads `historical_selections.json` at **module import time** (top-level `with open(...)`). If the file does not exist when the module is imported, the entire application will crash. This should be moved inside `video_sequence_gen()`.

**Key functions**:

| Function | Description |
|---|---|
| `Image_sequence_generation(scene_durations)` | Entry point. Iterates scenes, calls `video_sequence_gen` for each. |
| `video_sequence_gen(scene_ID, duration, aspect_ratio)` | Loads selected images, applies visual treatment, assembles MoviePy clips, exports MP4. |
| `apply_rounded_corners(pil_img, radius=40)` | Masks image to rounded rectangle. **Defined twice — duplicate.** |
| `add_rounded_blurred_border(pil_img, ...)` | Adds a dark blurred border around the image. |

**Aspect ratio dimensions**:
| Ratio | Width | Height |
|---|---|---|
| `4:3` | 1024 | 786 |
| `9:16` | 938 | 1664 |

**Canvas**: Always 1080×1920 (vertical reel). Images are centre-composited on a white background.

**Output**: `VIDEO/{scene_id}_sequence.mp4` at 24 fps.

---

### `Qwen_TTS.py`

**Role**: Standalone TTS generation via ComfyUI's `FB_Qwen3TTSVoiceClone` node.

**Not integrated with the UI.** Must be run as `python Qwen_TTS.py` and edited manually to set `target_text`.

**Workflow nodes**:
- `24`: `LoadAudio` — reference audio for voice cloning (`audio [vocals].mp3`)
- `40`: `FB_Qwen3TTSVoiceClone` — Qwen3 0.6B TTS, clones voice from `ref_audio`
- `21`: `SaveAudio` — saves FLAC to ComfyUI output folder

**Output**: `VOICE/node{node_id}_{index}.flac`

---

### `pipeline_tasks.py`

**Role**: Legacy async wrappers, now superseded by the wrappers in `MAIN_AI_PIPELINE.py`. Contains duplicate logic. Can be removed or kept as a reference.

Note: `run_WAN_I2V_Gen` in this file does not accept `positive_prompt` / `negative_prompt` parameters, unlike the version in `MAIN_AI_PIPELINE.py`.

---

### `main_app.py`

**Role**: An earlier version of `AI_App.py`. Lacks the Image Sequence Scenes tab, animation prompt handling, negative prompt handling, and `on_ready_callback`. Should not be used; kept for historical reference.

---

## Execution Order

```
1. python MAIN_AI_PIPELINE.py
2.   CorporateUIApp(on_ready_callback=start_pipeline)
3.   app.mainloop() → UI event loop starts
4.   [User pastes JSON and clicks Proceed]
5.   load_main_page()
6.     process_scenes(json_data)         ← parses JSON into 7 dicts
7.     write processed_output.json       ← persists parsed data
8.     setup_main_page()                 ← builds dashboard + image seq UI
9.     load_data()                        ← scans IMAGE/ + reads JSON
10.    display_current_scene()            ← renders image grid
11.    on_ready_callback(self)            ← fires start_pipeline(app)
12.      app.prepare_scenes()            ← extracts {scene, prompt} list
13.      threading.Thread(pipeline)      ← runs async pipeline in background
14.        asyncio.gather(run_Flux_Image_Gen × N)
15.          Flux_Image_Gen.run(prompt, scene_number)
16.            ComfyUI WebSocket → image generation
17.            save IMAGE/scene{N}_{idx}.png
18.            free_memory()
19.  [User reviews images in UI]
20.  [User clicks ▶ Video Process]
21.    video_process()
22.      Video_pipeline(video_jobs)
23.        asyncio.gather(run_WAN_I2V_Gen × N)
24.          WAN_I2V_Gen.run(image_path, pos, neg)
25.            ComfyUI WebSocket → video generation
26.            save VIDEO/scene{N}_node56_{idx}.mp4
27.            free_memory()
28.  [User switches to Image Sequence Scenes tab]
29.    load_image_seq_data()              ← loads historical_photos from JSON
30.    [User selects images, sets aspect ratio]
31.    finish_seq_selection()             ← writes historical_selections.json
32.    trigger_image_sequence_generation()
33.      Image_sequence_generation(scene_durations)
34.        video_sequence_gen(scene_id, duration, ratio)
35.          MoviePy → export VIDEO/{scene_id}_sequence.mp4
```

---

## Data Flow

```
[User JSON input]
        │
        ▼
process_scenes()
        │
        ├─ scene_visuals      → Image_pipeline → Flux_Image_Gen → IMAGE/*.png
        ├─ scene_animations   → Video_pipeline → WAN_I2V_Gen   → VIDEO/*.mp4
        ├─ scene_text         → (parsed, not yet rendered)
        ├─ vo_script          → Qwen_TTS (manual) → VOICE/*.flac
        ├─ scene_vo_lines     → (available in JSON, not yet used in export)
        ├─ scene_durations    → Image_sequence_generation → VIDEO/*_sequence.mp4
        └─ historical_photos  → UI: Image Sequence Scenes tab
                                      ↓ user selects images
                               historical_selections.json
                                      ↓
                               Image_sequence_generation
                                      ↓
                               VIDEO/{scene_id}_sequence.mp4
```

---

## ComfyUI API Protocol

All three generation modules (`Flux_Image_Gen`, `WAN_I2V_Gen`, `Qwen_TTS`) follow the same pattern:

```python
# 1. Generate a unique client ID
client_id = str(uuid.uuid4())

# 2. Open WebSocket connection
ws = websocket.WebSocket()
ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

# 3. Submit workflow
prompt_id = str(uuid.uuid4())
queue_prompt(prompt_dict, prompt_id, client_id)

# 4. Wait for completion
# Block on WebSocket, watching for:
#   {"type": "executing", "data": {"node": null, "prompt_id": "<our id>"}}
wait_for_completion(ws, prompt_id)

# 5. Retrieve output file list from history
history = get_history(prompt_id)[prompt_id]
# history["outputs"][node_id]["images"|"video"|"audio"][i] contains:
#   { "filename": "...", "subfolder": "...", "type": "output" }

# 6. Download each file from /view endpoint
# 7. Save locally
# 8. POST to /free to unload models
```

---

## JSON Pipeline

### Input format (raw LLM output)
An array of scene objects. The upstream LLM that produces this JSON is not part of this project. See `README.md → JSON Schema` for the full field reference.

### Intermediate format (`processed_output.json`)
Written by `process_scenes()` immediately after JSON submission. Seven top-level keys. This file is the source of truth for all downstream operations and is read by `load_data()`, `load_image_seq_data()`, and `Json_File_Parsing()`.

### Selection format (`historical_selections.json`)
Written by `finish_seq_selection()`. Maps scene IDs to selected image paths and aspect ratio:
```json
{
  "5": {
    "selected_images": ["D:\\...\\historical_photos\\image.jpg"],
    "aspect_ratio": "4:3"
  }
}
```

---

## Extension Points

### Adding a new generation backend
1. Create a module with a `run(...)` public function that returns a list of saved file paths
2. Add an async wrapper in `MAIN_AI_PIPELINE.py` following the `run_Flux_Image_Gen` pattern
3. Wire it into `AI_App.Image_pipeline()` or `Video_pipeline()` as appropriate

### Swapping ComfyUI workflows
Each generation module embeds its workflow as a `PROMPT_TEXT` JSON string constant. To use a different ComfyUI workflow:
1. Export the workflow from ComfyUI as JSON (API format)
2. Replace `PROMPT_TEXT` in the relevant module
3. Update the injection point — the line that sets `prompt["node_id"]["inputs"]["field"] = value`
4. Update `save_image` / `save_video` if the output node ID changes

### Adding on-screen text rendering
The `scene_text` data (`small`, `bold`, `large` fields) is already parsed and stored in `processed_output.json`. To render it:
1. After image generation, load the PNG with Pillow
2. Use `ImageDraw` to composite the text fields at defined positions
3. Save the modified image (or a copy) to the same `IMAGE/` directory

### Adding full video assembly
After all scene clips exist in `VIDEO/`, use MoviePy's `concatenate_videoclips()` to assemble them in scene order. The `scene_durations` and `scene_vo_lines` data is already available in `processed_output.json` for sync.

---

## Code Quality Notes

### Issues to address before 1.0

| Issue | Location | Severity |
|---|---|---|
| Hardcoded Windows paths (`D:\AI_Schemea`) | All modules | High |
| Debug print with profanity | `AI_App.py:process_scenes()` line ~42 | High |
| Module-level file read that crashes on import | `Image_Sequence_Scenes.py:17` | High |
| Duplicate `apply_rounded_corners` function | `Image_Sequence_Scenes.py` | Medium |
| `pipeline_tasks.py` is a duplicate of `MAIN_AI_PIPELINE.py` | `pipeline_tasks.py` | Medium |
| `main_app.py` is a superseded version of `AI_App.py` | `main_app.py` | Medium |
| `negative_prompts` dict referenced before assignment in some paths | `AI_App.py` | Medium |
| `test.PY` and `rfile.r` are uncommitted scratch files | Root dir | Low |
| Fixed random seed in Flux workflow (same seed every run) | `Flux_Image_Gen.py:PROMPT_TEXT` node 98:25 | Low |
| No error recovery if ComfyUI is unreachable | All gen modules | Medium |
| `Image_pipeline()` imported circularly via `MAIN_AI_PIPELINE` | `AI_App.py:regenerate_image()` | Medium |
