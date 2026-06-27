import websocket  # websocket-client: pip install websocket-client
import uuid
import json
import urllib.request
import urllib.parse
import os

# ── Configuration ────────────────────────────────────────────────────────────
SERVER_ADDRESS = "127.0.0.1:8188"
OUTPUT_FOLDER  = "D:/AI_Schemea/VOICE"          # <-- change this to your desired path
CLIENT_ID      = str(uuid.uuid4())
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def queue_prompt(prompt: dict, prompt_id: str) -> None:
    payload = {"prompt": prompt, "client_id": CLIENT_ID, "prompt_id": prompt_id}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{SERVER_ADDRESS}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req).read()


def get_audio_file(filename: str, subfolder: str, folder_type: str) -> bytes:
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": folder_type}
    )
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/view?{params}") as resp:
        return resp.read()


def get_history(prompt_id: str) -> dict:
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as resp:
        return json.loads(resp.read())


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


def generate_audio(ws: websocket.WebSocket, prompt: dict) -> dict[str, list[bytes]]:
    """
    Queue the prompt, wait for completion, then download every audio file
    produced by any node.

    Returns:
        { node_id: [audio_bytes, ...] }
    """
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id)
    wait_for_completion(ws, prompt_id)

    history     = get_history(prompt_id)[prompt_id]
    output_audio: dict[str, list[bytes]] = {}

    for node_id, node_output in history["outputs"].items():
        clips: list[bytes] = []

        # ComfyUI audio nodes store results under the "audio" key
        for key in ("audio", "audios"):
            if key in node_output:
                for item in node_output[key]:
                    audio_data = get_audio_file(
                        item["filename"], item["subfolder"], item["type"]
                    )
                    clips.append(audio_data)

        if clips:
            output_audio[node_id] = clips

    return output_audio


def save_audio(output_audio: dict[str, list[bytes]], folder: str) -> list[str]:
    """
    Save every audio clip to *folder*.
    Files are named  <node_id>_<index>.flac  (adjust extension if needed).

    Returns a list of saved file paths.
    """
    saved: list[str] = []
    for node_id, clips in output_audio.items():
        for idx, audio_bytes in enumerate(clips):
            filename = os.path.join(folder, f"node{node_id}_{idx}.flac")
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            print(f"  Saved → {filename}")
            saved.append(filename)
    return saved


# ── Workflow (paste your ComfyUI JSON here) ───────────────────────────────────
PROMPT_TEXT = """
{
  "21": {
    "inputs": {
      "filename_prefix": "audio/ComfyUI",
      "audioUI": "",
      "audio": [
        "40",
        0
      ]
    },
    "class_type": "SaveAudio",
    "_meta": {
      "title": "Save Audio (FLAC)"
    }
  },
  "24": {
    "inputs": {
      "audio": "audio [vocals].mp3",
      "audioUI": "/api/view?filename=audio%20%5Bvocals%5D.mp3&type=input&subfolder=&rand=0.7741705444247814"
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  },
  "40": {
    "inputs": {
      "target_text": "What almost killed Wikipedia in 2005?\nExplosive growth flooded the site, edits poured in.\nAnyone could edit, which was brilliant and risky.\nVandalism and hoaxes spread fast, unnoticed at first.\nThen the Seigenthaler hoax hit the headlines.\nA respected journalist was falsely accused, reputation was damaged.\nMainstream media criticized Wikipedia's reliability and public trust fell.\nVolunteer editors burned out and many left.\nEdit wars made pages unstable, facts flipped back and forth.\nLegal worries and reputation risk multiplied, pressure grew,\nLeadership faced a crisis and they acted quickly.\nThey added page protection and emergency rules,\nAdmin tools improved and vandals were caught faster,\nSourcing rules tightened, citations became vital,\nCommunity governance matured with votes and arbitration.\nTransparency and fundraising rebuilt some public trust.\nJournalists and scholars began checking entries again,\nOpenness stayed but guardrails were added.\nWikipedia survived by learning and changing its rules,\nToday it is cautious and still a global knowledge hub.\"\n",
      "model_choice": "0.6B",
      "device": "cuda",
      "precision": "bf16",
      "language": "English",
      "ref_text": "It's didn't work in India in 2008. Directions were unusable, as some streets didn't have names. But street names were the foundation of Google Maps, two researchers flew to India to figure it out. They asked businesses for directions, got people to sketch maps, and even followed strangers to see how they navigated unfamiliar places. They discovered that people use landmarks, not street names. Navigation involved four critical elements. Orientation, head towards the water. Description of a turn. Turn just past the big bazaar. Confirmation of the right path. You'll see a petrol station on the right. Error correction. If you reach the roundabout, you've gone too far. With these four elements, Google successfully localized maps and took full advantage of landmarks. That's why today your directions in India often say \"turn left after the temple\" instead of just a street name.",
      "seed": 682779102015929,
      "max_new_tokens": 2048,
      "top_p": 0.9,
      "top_k": 70,
      "temperature": 0.8,
      "repetition_penalty": 1.05,
      "x_vector_only": false,
      "attention": "sdpa",
      "unload_model_after_generate": true,
      "custom_model_path": "",
      "ref_audio": [
        "24",
        0
      ]
    },
    "class_type": "FB_Qwen3TTSVoiceClone",
    "_meta": {
      "title": "🎭 Qwen3-TTS VoiceClone"
    }
  }
}
"""
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    prompt = json.loads(PROMPT_TEXT)

    # ── Optional: tweak prompt values programmatically before sending ──────
    # prompt["40"]["inputs"]["target_text"] = "Your new script here"
    # prompt["40"]["inputs"]["seed"]        = 12345
    # ──────────────────────────────────────────────────────────────────────

    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    print("Connected to ComfyUI – generating audio …")

    try:
        output_audio = generate_audio(ws, prompt)
    finally:
        ws.close()

    if not output_audio:
        print("No audio output received. Check your workflow nodes.")
        return

    print(f"\nSaving audio to '{OUTPUT_FOLDER}' …")
    saved_files = save_audio(output_audio, OUTPUT_FOLDER)
    print(f"\nDone – {len(saved_files)} file(s) saved.")


if __name__ == "__main__":
    main()