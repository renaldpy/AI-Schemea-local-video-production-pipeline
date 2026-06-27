# 🎬 AI Schemea — Documentary Video Production Pipeline

> **Status: Work In Progress** — Core image and video generation pipelines are functional. TTS, on-screen text rendering, and full automated assembly are under active development.

AI Schemea is a **local AI-powered documentary video production tool**. It takes a structured JSON description of a video's scenes and drives a full generation pipeline: producing images via **Flux 2** and converting them to short video clips via **Wan 2.1 Image-to-Video**, all orchestrated through a local **ComfyUI** instance. A **Tkinter desktop UI** provides scene-by-scene prompt editing, image review, image selection for  photo slideshows, and video generation control.

The project was built for documentary-style short-form content — think YouTube explainers or social media reels — where each scene has a visual, a voiceover line, and optional motion.

---

## ✨ Features

- **Scene-driven JSON pipeline** — paste a structured JSON payload and the app parses it into visual prompts, animation prompts, on-screen text, VO lines, and durations
- **AI image generation** — sends prompts to ComfyUI running Flux 2 (GGUF-quantised), with optional Charcoal LoRA for stylised illustration output
- **AI video generation** — converts approved images to short video clips using Wan 2.1 I2V (14B, GGUF), with per-scene positive and negative motion prompts
- ** photo slideshow builder** — select real archival photos for documentary scenes, assign aspect ratios (4:3 / 9:16), and export polished slideshow clips with rounded corners, blurred borders, and click SFX via MoviePy
- **AI voice-over via TTS** — Qwen3-TTS voice cloning through ComfyUI generates narration in FLAC format
- **Dark corporate UI** — scene browser with image grid, editable prompt fields, Keep & Delete Rest, Edit Prompt & Regenerate, and Video Process controls
- **Async parallel generation** — up to 4 concurrent image or video jobs using `asyncio` + `ThreadPoolExecutor`
- **Reference image download** — scenes with a `reference_visual` URL have the image auto-downloaded instead of being AI-generated

---

## 📸 Screenshots

> *Screenshots to be added — the application runs as a local desktop window and requires ComfyUI to be running.*

---

## 🛠 Requirements

### Software
| Requirement | Version |
|---|---|
| Python | 3.10+ |
| ComfyUI | Latest (running locally on `127.0.0.1:8188`) |
| Windows | Tested on Windows 10/11 (paths are Windows-style by default) |

### Python Packages
```
pillow
websocket-client
moviepy
numpy
```

Install with:
```bash
pip install pillow websocket-client moviepy numpy
```

### ComfyUI Models Required

**Image Generation (Flux 2)**
- `flux-2-klein-4b-Q8_0.gguf` — UNet (GGUF)
- `flux2-vae.safetensors` — VAE
- `qwen_3_4b_fp4_flux2.safetensors` — CLIP
- `Charcoal_E5.safetensors` — LoRA (optional, toggleable)

**Video Generation (Wan 2.1 I2V)**
- `wan2.1-i2v-14b-480p-Q3_K_S.gguf` — UNet (GGUF)
- `wan_2.1_vae.safetensors` — VAE
- `umt5_xxl_fp8_e4m3fn_scaled.safetensors` — CLIP
- `clip_vision_h.safetensors` — CLIP Vision
- `lightx2v_I2V_14B_480p_cfg_step_distill_rank16_bf16.safetensors` — LoRA

**TTS (Qwen3)**
- `FB_Qwen3TTSVoiceClone` ComfyUI custom node (0.6B model)

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-schemea.git
cd ai-schemea
```

### 2. Install dependencies
```bash
pip install pillow websocket-client moviepy numpy
```

### 3. Configure paths

Open `AI_App.py` and update the base directory constant:
```python
BASE_DIR = r"C:\path\to\your\ai-schemea"
```

Do the same for `Flux_Image_Gen.py` and `WAN_I2V_Gen.py`:
```python
OUTPUT_FOLDER = "C:/path/to/your/ai-schemea/IMAGE"
OUTPUT_FOLDER = "C:/path/to/your/ai-schemea/VIDEO"
```

### 4. Start ComfyUI
Ensure ComfyUI is running locally and accessible at `http://127.0.0.1:8188`.

### 5. Place models
Place all required model files in your ComfyUI `models/` directory as appropriate (unet, vae, clip, loras).

### 6. Run the application
```bash
python MAIN_AI_PIPELINE.py
```

---

## 🗂 Project Structure

```
ai-schemea/
│
├── MAIN_AI_PIPELINE.py         # Entry point — launches UI and starts pipeline
├── AI_App.py                   # Main Tkinter UI + JSON parsing + pipeline coordination
├── Flux_Image_Gen.py           # ComfyUI image generation via Flux 2
├── WAN_I2V_Gen.py              # ComfyUI video generation via Wan 2.1 I2V
├── Image_Sequence_Scenes.py    #  photo slideshow assembly (MoviePy)
├── Qwen_TTS.py                 # ComfyUI TTS generation via Qwen3-TTS
├── pipeline_tasks.py           # Legacy async task wrappers (superseded by AI_App.py)
├── main_app.py                 # Legacy UI (superseded by AI_App.py)
├── verify_imports.py           # Import health check script
├── test.PY                     # Development scratch file
├── rfile.r                     # Empty placeholder
│
├── Text_Files/
│   ├── processed_output.json   # Parsed scene data (auto-generated from UI input)
│   └── _selections.json  # User image selections + aspect ratios
│
├── IMAGE/                      # Generated images (scene{N}_{index}.png)
├── VIDEO/                      # Generated video clips (scene{N}_node56_{index}.mp4)
├── VOICE/                      # Generated TTS audio (node{N}_{index}.flac)
├── _photos/          # Archival/reference images for documentary scenes
├── SFX/
│   └── click.mp3               # Sound effect used in slideshow transitions
│
├── downloads/                  # Scratch download folder
├── wiki_downloads/             # Reference images downloaded during a session
│
└── .vscode/
    └── launch.json             # VS Code debug configuration
```

---

## ⚙️ Complete Workflow

### Phase 1 — Input & Parsing
1. User launches the app via `MAIN_AI_PIPELINE.py`
2. The **System Initialization** screen accepts a raw JSON payload (the scene description produced by an upstream LLM, not included in this project)
3. `process_scenes()` in `AI_App.py` parses the JSON into seven structured data streams and writes `processed_output.json`

### Phase 2 — Image Generation
4. Scenes with a `primary_visual_image` prompt are passed to `Flux_Image_Gen.run()`
5. Each call connects to ComfyUI via WebSocket, injects the prompt into the Flux 2 workflow, waits for completion, and saves `scene{N}_{index}.png` to `IMAGE/`
6. Scenes with a `reference_visual` URL skip generation — the image is downloaded instead
7. Up to 4 scenes generate in parallel via `asyncio.gather`

### Phase 3 — Review & Edit
8. The **Dashboard** view loads all generated images grouped by scene
9. User browses scenes (Previous / Next Batch), edits image prompts, animation prompts, and negative video prompts inline
10. **Keep & Delete Rest** removes unwanted batch variants; **Edit Prompt & Regen** re-runs image generation for a single scene with the updated prompt

### Phase 4 — Video Generation
11. **▶ Video Process** iterates over all scenes with non-null animation prompts
12. Each image is sent to `WAN_I2V_Gen.run()` with its positive and negative motion prompts
13. ComfyUI runs the Wan 2.1 I2V workflow (480p, 49 frames at 16 fps, ≈3 s clips) and saves MP4s to `VIDEO/`

### Phase 5 —  Photo Sequences
14. The **Image Sequence Scenes** tab shows scenes flagged as `_photo: true`
15. User browses archival images from `_photos/`, selects images per scene, and sets an aspect ratio (4:3 or 9:16)
16. **Finish Selection** saves choices to `_selections.json`
17. **🖼 Generate Image Scenes** calls `Image_sequence_generation()` via MoviePy:
    - Distributes scene duration equally across selected images
    - Applies rounded corners and blurred dark borders
    - Composites images on a white canvas
    - Adds a click SFX on every transition except the last
    - Exports `{scene_id}_sequence.mp4` to `VIDEO/`

### Phase 6 — Voice-Over (Manual)
18. `Qwen_TTS.py` is a standalone script — run it separately to generate narration
19. It sends the combined `vo_script` to ComfyUI's Qwen3-TTS node with a reference audio sample for voice cloning
20. Audio is saved as FLAC to `VOICE/`

---

## 📐 JSON Schema

The application accepts an array of scene objects. Each object may contain the following fields:

```jsonc
[
  {
    // REQUIRED
    "scene": 1,                          // integer — scene number (used for file naming)

    // VISUAL (mutually exclusive with _photo / reference_visual)
    "primary_visual_image": "...",        // string | null — Flux 2 image prompt
    "animation": "...",                  // string | null — Wan I2V positive motion prompt
    "negative_video_prompt": "...",      // string | null — Wan I2V negative motion prompt

    //  PHOTO MODE (overrides image generation)
    "_photo": false,           // boolean — if true, skip image gen; use archival photos
    "_photo_description": "...", // string — description shown in UI ( mode)

    // REFERENCE VISUAL MODE (overrides image generation)
    "reference_visual": null,            // string | null — URL of an image to download instead

    // ON-SCREEN TEXT
    "on_screen_text_small": "The year was",  // string — small caption text
    "on_screen_text_bold": "KILLED WIKIPEDIA", // string — large bold headline text
    "on_screen_text_large": "2005",          // string — large display text

    // NARRATION
    "vo_line": "What almost killed Wikipedia back in 2005?", // string — voiceover line

    // TIMING
    "duration_seconds": 4                // integer — clip duration
  }
]
```

### Visual Mode Logic

| `_photo` | `reference_visual` | `primary_visual_image` | Behaviour |
|---|---|---|---|
| `false` | `null` | string | AI image generated via Flux 2 |
| `false` | URL string | (ignored) | Image downloaded from URL |
| `true` | (ignored) | (ignored) | Archival photo selected manually in UI |

### Processed Output Schema (`processed_output.json`)

After parsing, the app writes a structured file with seven top-level keys:

```jsonc
{
  "scene_visuals":    [{ "scene": 1, "primary_visual_image": "..." }],
  "scene_animations": [{ "scene": 1, "animation": "...", "negative_video_prompt": "..." }],
  "scene_text":       [{ "scene": 1, "small": "...", "bold": "...", "large": "..." }],
  "vo_script":        "Combined VO narration as a single string",
  "scene_vo_lines":   [{ "scene": 1, "vo_line": "..." }],
  "scene_durations":  [{ "scene": 1, "duration_seconds": 4 }],
  "_photos":[{ "scene": 6, "_photo_description": "...", "vo_line": "...", "duration_seconds": 5 }]
}
```

---

## 🧩 ComfyUI Integration

Both image and video generation use the same ComfyUI API pattern:

1. Connect via WebSocket at `ws://127.0.0.1:8188/ws?clientId={uuid}`
2. POST the workflow JSON to `/prompt`
3. Listen for `executing` messages until `node == null` for the current `prompt_id`
4. Fetch output files from `/view?filename=...`
5. Save locally; POST to `/free` to unload models from VRAM

### Image Workflow (Flux 2)
- **UNet**: `UnetLoaderGGUF` → `flux-2-klein-4b-Q8_0.gguf`
- **LoRA** (optional): `Charcoal_E5.safetensors` at strength 2 (toggled by `ComfySwitchNode`)
- **CLIP**: `CLIPLoader` → `qwen_3_4b_fp4_flux2.safetensors`
- **Sampler**: `SamplerCustomAdvanced` with Euler, 20–22 steps
- **Output**: `SaveImage` → 4 images per call at 1024×1024

### Video Workflow (Wan 2.1 I2V)
- **UNet**: `UnetLoaderGGUF` → `wan2.1-i2v-14b-480p-Q3_K_S.gguf`
- **LoRA**: `lightx2v_I2V_14B_480p_cfg_step_distill_rank16_bf16.safetensors`
- **CLIP**: `CLIPLoader` → `umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- **CLIP Vision**: `CLIPVisionLoader` → `clip_vision_h.safetensors`
- **Node**: `WanImageToVideo` at 480×480, 49 frames
- **Output**: `SaveVideo` via `CreateVideo` at 16 fps → MP4

---

## 🗺 Roadmap

### Implemented
- [x] JSON scene parsing and structured data extraction
- [x] Async parallel image generation via Flux 2 + ComfyUI
- [x] Async parallel video generation via Wan 2.1 I2V + ComfyUI
- [x] Dark theme Tkinter UI with scene browser
- [x] Inline prompt editing and single-scene regeneration
- [x] Keep & Delete Rest for batch management
- [x]  photo slideshow builder with MoviePy
- [x] Per-scene aspect ratio selection (4:3 / 9:16)
- [x] Rounded corner + blurred border image treatment
- [x] Click SFX on slideshow transitions
- [x] TTS voice-over generation via Qwen3-TTS (standalone script)
- [x] Reference image auto-download from URL
- [x] VRAM free after each generation job

### Planned / In Progress
- [ ] On-screen text rendering — `scene_text` fields (`small`, `bold`, `large`) are parsed but not yet composited onto images or video
- [ ] Full automated assembly — no final video concatenation step exists yet; clips must be assembled manually
- [ ] LLM integration — the upstream prompt that generates the input JSON is not part of this codebase
- [ ] TTS integration into UI — `Qwen_TTS.py` is standalone; it is not triggered from the main UI
- [ ] Audio-visual sync — VO timing relative to scene durations is not yet enforced in export
- [ ] Cross-platform path handling — all paths are currently hardcoded Windows strings
- [ ] Configuration file — `SERVER_ADDRESS`, `BASE_DIR`, and `OUTPUT_FOLDER` are scattered constants

---

## ⚠️ Known Limitations

- **Hardcoded Windows paths** — `BASE_DIR = r"D:\AI_Schemea"` and similar constants must be manually updated
- **ComfyUI must be running** — the app will crash at generation time if ComfyUI is not available on `127.0.0.1:8188`
- **No LLM included** — the JSON input must be created externally (e.g., from Claude, GPT-4, or another LLM)
- **No final assembly** — individual MP4 clips and slideshow sequences are not merged into a finished video
- **TTS is manual** — `Qwen_TTS.py` must be run separately and the script text edited by hand
- **No `.env` or config file** — all configuration is inline in source files
- **Debug print remains** — a `print("NIGAAAAAAAAAAA: ...")` debug line is present in `process_scenes()` and should be removed
- **`apply_rounded_corners` is defined twice** — duplicate function definition in `Image_Sequence_Scenes.py`
- **`Image_Sequence_Scenes.py` reads JSON at module load time** — the `with open(...)` call at the top level runs on import, which will crash if the file does not exist

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

See [LICENSE](LICENSE).
"# AI-Schemea-local-video-production-pipeline" 
