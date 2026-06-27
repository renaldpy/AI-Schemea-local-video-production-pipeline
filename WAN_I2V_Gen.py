import websocket
import uuid
import json
import urllib.request
import urllib.parse
import os


# ── Configuration ─────────────────────────────────────────────────────────────
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_FOLDER  = "D:/AI_Schemea/VIDEO"
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_FOLDER, exist_ok=True)




def queue_prompt(prompt: dict, prompt_id: str, client_id: str) -> dict:
    payload = {"prompt": prompt, "client_id": client_id, "prompt_id": prompt_id}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{SERVER_ADDRESS}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())


def get_video_file(filename: str, subfolder: str, folder_type: str) -> bytes:
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": folder_type}
    )
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/view?{params}") as resp:
        return resp.read()


def get_history(prompt_id: str) -> dict:
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as resp:
        return json.loads(resp.read())


def wait_for_completion(ws: websocket.WebSocket, prompt_id: str) -> None:
    while True:
        out = ws.recv()
        if isinstance(out, str):
            msg = json.loads(out)
            if msg.get("type") == "executing":
                data = msg["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break


PROMPT_TEXT = """
{
  "3": {
    "inputs": {
      "seed": 1101259488187655,
      "steps": 11,
      "cfg": 5.4,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": [
        "54",
        0
      ],
      "positive": [
        "50",
        0
      ],
      "negative": [
        "50",
        1
      ],
      "latent_image": [
        "50",
        2
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "6": {
    "inputs": {
      "text": "the object spins extremely slowly on a vertical rotation only at 1% speed moving anti-clockwise, ;arge hairline fracture slowly forming on the object, volumetric god rays leaking through the widest crack, subtle chromatic aberration on crack edges, photorealistic surface texture, shallow depth of field, smooth motion and constant motion",
      "clip": [
        "38",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "7": {
    "inputs": {
      "text": "close up, zoomed in, fast movement, shaky, jerky, jump cut, flickering, deformed, morphing, camera tilt, zoom in, blurry, low quality, watermark, jitter, stutter, horizontal rotation, fast rotation, clockwise rotatiom, horizontal axis rotation, horizontal rotation, small cracks forming.",
      "clip": [
        "38",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Negative Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "3",
        0
      ],
      "vae": [
        "39",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "38": {
    "inputs": {
      "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
      "type": "wan",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "39": {
    "inputs": {
      "vae_name": "wan_2.1_vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "49": {
    "inputs": {
      "clip_name": "clip_vision_h.safetensors"
    },
    "class_type": "CLIPVisionLoader",
    "_meta": {
      "title": "Load CLIP Vision"
    }
  },
  "50": {
    "inputs": {
      "width": 480,
      "height": 480,
      "length": 49,
      "batch_size": 1,
      "positive": [
        "6",
        0
      ],
      "negative": [
        "7",
        0
      ],
      "vae": [
        "39",
        0
      ],
      "clip_vision_output": [
        "51",
        0
      ],
      "start_image": [
        "52",
        0
      ]
    },
    "class_type": "WanImageToVideo",
    "_meta": {
      "title": "WanImageToVideo"
    }
  },
  "51": {
    "inputs": {
      "crop": "none",
      "clip_vision": [
        "49",
        0
      ],
      "image": [
        "52",
        0
      ]
    },
    "class_type": "CLIPVisionEncode",
    "_meta": {
      "title": "CLIP Vision Encode"
    }
  },
  "52": {
    "inputs": {
      "image": "25-259087_transparent-wikipedia-logo-png-png-download.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "54": {
    "inputs": {
      "shift": 8,
      "model": [
        "59",
        0
      ]
    },
    "class_type": "ModelSamplingSD3",
    "_meta": {
      "title": "ModelSamplingSD3"
    }
  },
  "55": {
    "inputs": {
      "fps": 16,
      "images": [
        "8",
        0
      ]
    },
    "class_type": "CreateVideo",
    "_meta": {
      "title": "Create Video"
    }
  },
  "56": {
    "inputs": {
      "filename_prefix": "video/ComfyUI",
      "format": "auto",
      "codec": "auto",
      "video-preview": "",
      "video": [
        "55",
        0
      ]
    },
    "class_type": "SaveVideo",
    "_meta": {
      "title": "Save Video"
    }
  },
  "58": {
    "inputs": {
      "unet_name": "wan2.1-i2v-14b-480p-Q3_K_S.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Unet Loader (GGUF)"
    }
  },
  "59": {
    "inputs": {
      "lora_name": "lightx2v_I2V_14B_480p_cfg_step_distill_rank16_bf16.safetensors",
      "strength_model": 1,
      "model": [
        "58",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  }
}
"""

def free_memory() -> None:
    """Unload all models and free ComfyUI node/model cache."""
    # Free model cache
    req = urllib.request.Request(
        f"http://{SERVER_ADDRESS}/free",
        data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req).read()
    print("  VRAM freed & models unloaded.")


def generate_video(ws: websocket.WebSocket, prompt: dict, client_id: str) -> dict[str, list[bytes]]:
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id, client_id)
    wait_for_completion(ws, prompt_id)

    history = get_history(prompt_id)[prompt_id]
    output_video: dict[str, list[bytes]] = {}

    for node_id, node_output in history["outputs"].items():
        clips: list[bytes] = []
        for key in ("video", "videos", "gifs", "images"):
            if key in node_output:
                for item in node_output[key]:
                    video_data = get_video_file(
                        item["filename"], item["subfolder"], item["type"]
                    )
                    clips.append((item["filename"], video_data))
        if clips:
            output_video[node_id] = clips

    return output_video


def save_video(output_video: dict, folder: str, input_image_path: str = "") -> list[str]:
    saved: list[str] = []
    prefix = ""
    if input_image_path:
        base_name = os.path.basename(input_image_path)
        scene_part = base_name.split('_')[0]
        prefix = f"{scene_part}_"

    for node_id, clips in output_video.items():
        for idx, (original_filename, video_bytes) in enumerate(clips):
            ext = os.path.splitext(original_filename)[-1] or ".mp4"
            filename = os.path.join(folder, f"{prefix}node{node_id}_{idx}{ext}")
            with open(filename, "wb") as f:
                f.write(video_bytes)
            print(f"  Saved → {filename}")
            saved.append(filename)
    return saved


def run(input_image_path: str, positive_prompt: str = "", negative_prompt: str = "") -> list[str]:
    """
    Entry point called by main.py.
    Accepts the image path, injects it into the prompt, runs video generation.
    """
    print(f"[VIDEO] Starting video generation for: {input_image_path}")
    prompt = json.loads(PROMPT_TEXT)

    # ── Inject the input image ────────────────────────────────────────────────
    prompt["52"]["inputs"]["image"] = input_image_path
    # ─────────────────────────────────────────────────────────────────────────

    prompt["6"]["inputs"]["text"] = positive_prompt
    prompt["7"]["inputs"]["text"] = negative_prompt

    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={client_id}")
    print(f"[VIDEO] Connected to ComfyUI with clientId: {client_id} …")

    try:
        output_video = generate_video(ws, prompt, client_id)
    finally:
        ws.close()

    if not output_video:
        print("[VIDEO] No video output received.")
        return []

    print(f"[VIDEO] Saving to '{OUTPUT_FOLDER}' …")
    saved = save_video(output_video, OUTPUT_FOLDER, input_image_path=input_image_path)
    print(f"[VIDEO] Done – {len(saved)} file(s) saved.")

    free_memory() 
    
    return saved


if __name__ == "__main__":
    # ── Standalone test: point to any image on disk ───────────────────────────
    run("D:/AI_Schemea/IMAGE/test.png")