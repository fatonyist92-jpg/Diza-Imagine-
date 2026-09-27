from gradio_client import Client, handle_file
import os, shutil

SPACE="MiniMaxAI/MiniMax-H3-Turbo-Lora"
PROMPT="The fox looks around, then trots deeper into the forest"
IMAGE_URL="https://huggingface.co/spaces/MiniMaxAI/MiniMax-H3-Turbo-Lora/resolve/main/examples/first.png"
OUT="minimax_h3_10s.mp4"

print("Connecting:", SPACE, flush=True)
client=Client(SPACE, verbose=True)
print("API SPEC:", client.view_api(return_format="dict"), flush=True)
print("Submitting 10s I2V...", flush=True)

result=client.predict(
    prompt=PROMPT,
    image_path=handle_file(IMAGE_URL),
    last_image_path=None,
    canvas="960x544 · 16:9 fast",
    duration=10,
    steps=4,
    seed=42,
    upsample=False,
    api_name="/generate",
)

print("RAW RESULT:", result, flush=True)
video=result[0]
path=getattr(video, "path", None) or (video if isinstance(video, str) else None)
if not path or not os.path.exists(path):
    raise RuntimeError(f"No local MP4 returned: {video!r}")

shutil.copyfile(path, OUT)
size=os.path.getsize(OUT)
print("MP4:", OUT, "bytes=", size, flush=True)
if size < 10000:
    raise RuntimeError("MP4 too small")
