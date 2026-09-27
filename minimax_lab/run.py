from gradio_client import Client, handle_file
import os, shutil

SPACE="MiniMaxAI/MiniMax-H3-Turbo-Lora"
PROMPT="The fox looks around, then trots deeper into the forest"
IMAGE_URL="https://huggingface.co/spaces/MiniMaxAI/MiniMax-H3-Turbo-Lora/resolve/main/examples/first.png"
OUT="minimax_h3_10s.mp4"

print("Connecting:", SPACE, flush=True)
client=Client(SPACE, verbose=True)
print("Submitting official workflow endpoint /output_video: 10s, 4 steps, larry Turbo LoRA", flush=True)

result=client.predict(
    PROMPT,
    handle_file(IMAGE_URL),
    None,
    "544x544 · 1:1 fast",
    10,
    4,
    42,
    False,
    "larry",
    api_name="/output_video",
)

print("RAW RESULT:", result, flush=True)
video=result[0]
path=getattr(video, "path", None) or (video if isinstance(video, str) else None)
if not path or not os.path.exists(path):
    raise RuntimeError(f"No local MP4 returned: {video!r}")

shutil.copyfile(path, OUT)
size=os.path.getsize(OUT)
print("REPORT:", result[1], flush=True)
print("MP4:", OUT, "bytes=", size, flush=True)
if size < 10000:
    raise RuntimeError("MP4 too small")
