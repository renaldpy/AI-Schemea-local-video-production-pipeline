#This is an example that uses the websockets api and the SaveImageWebsocket node to get images directly without
#them being saved to disk

import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import os

# ── Configuration ────────────────────────────────────────────────────────────
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_FOLDER  = "D:/AI_Schemea/IMAGE"

# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_FOLDER, exist_ok=True)



def queue_prompt(prompt, prompt_id, client_id):
    payload = {"prompt": prompt, "client_id": client_id, "prompt_id": prompt_id}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"http://{SERVER_ADDRESS}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )    
    return json.loads(urllib.request.urlopen(req).read())

def get_image_file(filename: str, subfolder: str, folder_type: str) -> bytes:
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": folder_type}
    )
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/view?{params}") as resp:
        return resp.read()



def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(SERVER_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())
    
def wait_for_completion(ws: websocket.WebSocket, prompt_id: str) -> None:
    """Block until ComfyUI signals that this prompt has finished executing."""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            msg = json.loads(out)
            if msg.get("type") == "executing":
                data = msg["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # done
        # binary frames are preview data – ignore them




PROMPT_TEXT = """
{
  "9": {
    "inputs": {
      "filename_prefix": "Flux2_dev",
      "images": [
        "98:8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "98:22": {
    "inputs": {
      "model": [
        "98:102",
        0
      ],
      "conditioning": [
        "98:26",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "BasicGuider"
    }
  },
  "98:16": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "98:10": {
    "inputs": {
      "vae_name": "flux2-vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "98:13": {
    "inputs": {
      "noise": [
        "98:25",
        0
      ],
      "guider": [
        "98:22",
        0
      ],
      "sampler": [
        "98:16",
        0
      ],
      "sigmas": [
        "98:48",
        0
      ],
      "latent_image": [
        "98:47",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "98:8": {
    "inputs": {
      "samples": [
        "98:13",
        0
      ],
      "vae": [
        "98:10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "98:38": {
    "inputs": {
      "clip_name": "qwen_3_4b_fp4_flux2.safetensors",
      "type": "flux2",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "98:48": {
    "inputs": {
      "steps": [
        "98:103",
        0
      ],
      "width": 1024,
      "height": 1024
    },
    "class_type": "Flux2Scheduler",
    "_meta": {
      "title": "Flux2Scheduler"
    }
  },
  "98:102": {
    "inputs": {
      "switch": [
        "98:104",
        0
      ],
      "on_false": [
        "98:105",
        0
      ],
      "on_true": [
        "98:101",
        0
      ]
    },
    "class_type": "ComfySwitchNode",
    "_meta": {
      "title": "Switch(model)"
    }
  },
  "98:100": {
    "inputs": {
      "value": 20
    },
    "class_type": "PrimitiveInt",
    "_meta": {
      "title": "Steps"
    }
  },
  "98:6": {
    "inputs": {
      "text": "",
      "clip": [
        "98:38",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "98:47": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 4
    },
    "class_type": "EmptyFlux2LatentImage",
    "_meta": {
      "title": "Empty Flux 2 Latent"
    }
  },
  "98:101": {
    "inputs": {
      "lora_name": "Charcoal_E5.safetensors",
      "strength_model": 2,
      "model": [
        "98:105",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "98:99": {
    "inputs": {
      "value": 22
    },
    "class_type": "PrimitiveInt",
    "_meta": {
      "title": "Steps"
    }
  },
  "98:25": {
    "inputs": {
      "noise_seed": 500436027408101
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "98:26": {
    "inputs": {
      "guidance": 3,
      "conditioning": [
        "98:6",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "FluxGuidance"
    }
  },
  "98:104": {
    "inputs": {
      "value": true
    },
    "class_type": "PrimitiveBoolean",
    "_meta": {
      "title": "Enable Turbo LoRA"
    }
  },
  "98:103": {
    "inputs": {
      "switch": [
        "98:104",
        0
      ],
      "on_false": [
        "98:100",
        0
      ],
      "on_true": [
        "98:99",
        0
      ]
    },
    "class_type": "ComfySwitchNode",
    "_meta": {
      "title": "Switch(steps)"
    }
  },
  "98:105": {
    "inputs": {
      "unet_name": "flux-2-klein-4b-Q8_0.gguf"
    },
    "class_type": "UnetLoaderGGUF",
    "_meta": {
      "title": "Unet Loader (GGUF)"
    }
  }
}"""

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


def generate_image(ws: websocket.WebSocket, prompt: dict, client_id: str) -> dict[str, list[bytes]]:
    """
    Queue the prompt, wait for completion, then download every image file
    produced by any node.

    Returns:
        { node_id: [image_bytes, ...] }
    """
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id, client_id)
    wait_for_completion(ws, prompt_id)

    history = get_history(prompt_id)[prompt_id]
    output_image: dict[str, list[bytes]] = {}

    for node_id, node_output in history["outputs"].items():
        clips: list[bytes] = []

        # ComfyUI image nodes store results under the "image" key
        for key in ("image", "images"):
            if key in node_output:
                for item in node_output[key]:
                    image_data = get_image_file(
                        item["filename"], item["subfolder"], item["type"]
                    )
                    clips.append(image_data)

        if clips:
            output_image[node_id] = clips

    return output_image


def save_image(output_image: dict[str, list[bytes]], folder: str, scene_number: int) -> list[str]:
    saved: list[str] = []

    for node_id, clips in output_image.items():
        for idx, image_bytes in enumerate(clips):

            filename = os.path.join(
                folder,
                f"scene{scene_number}_{idx}.png"
            )

            with open(filename, "wb") as f:
                f.write(image_bytes)

            print(f"  Saved → {filename}")
            saved.append(filename)

    return saved


def run(parament_ImgPrompt, scene_number) -> list[str]:
    """
    Entry point called by main.py.
    Runs image generation and returns a list of saved file paths.
    """
    print("[IMAGE] Starting image generation …")

    prompt = json.loads(PROMPT_TEXT)
    client_id = str(uuid.uuid4())

 
    # ── Tweak prompt values here if needed ────────────────────────────────────
    prompt["98:6"]["inputs"]["text"] = parament_ImgPrompt
    # prompt["98:25"]["inputs"]["noise_seed"] = 99999
    # ─────────────────────────────────────────────────────────────────────────
 
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={client_id}")
    print("[IMAGE] Connected to ComfyUI …")
 
    try:
        output_image = generate_image(ws, prompt, client_id)
    finally:
        ws.close()
 
    if not output_image:
        print("[IMAGE] No image output received.")
        return []
 
    print(f"[IMAGE] Saving to '{OUTPUT_FOLDER}' …")
    saved = save_image(output_image, OUTPUT_FOLDER, scene_number)
    print(f"[IMAGE] Done – {len(saved)} file(s) saved.")

    free_memory() 
    return saved
 
 
if __name__ == "__main__":
    run(parament_ImgPrompt="2 balls attatched to a thick rod")