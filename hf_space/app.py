import os
import uuid

import gradio as gr
import spaces
import torch
from PIL import ImageOps
from diffusers import HunyuanVideo15ImageToVideoPipeline
from diffusers.utils import export_to_video

MODEL_ID = "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_i2v_step_distilled"
NUM_FRAMES = 121
NUM_INFERENCE_STEPS = 4
FPS = 24
GUIDANCE = 1.0
OUTPUT_DIR = "/tmp/diza_hunyuan"

# ZeroGPU supports CUDA placement at module level through its CUDA emulation layer.
# device_map="cuda" avoids keeping a second full copy of this large model in CPU RAM.
pipe = HunyuanVideo15ImageToVideoPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
pipe.vae.enable_tiling()


def _prepare_image(image):
    if image is None:
        raise gr.Error("Upload image dulu.")
    image = ImageOps.exif_transpose(image).convert("RGB")
    # Preserve aspect ratio, keep dimensions friendly to the video VAE.
    w, h = image.size
    max_side = 832
    scale = min(1.0, max_side / max(w, h))
    w = max(64, (int(w * scale) // 16) * 16)
    h = max(64, (int(h * scale) // 16) * 16)
    return image.resize((w, h))


@spaces.GPU(duration=80)
def generate(input_image, prompt, seed):
    prompt = "" if prompt is None else str(prompt)
    if not prompt.strip():
        raise gr.Error("Prompt masih kosong.")

    source = _prepare_image(input_image)
    seed = int(seed) if seed is not None and int(seed) >= 0 else int(torch.randint(0, 2**31 - 1, (1,)).item())
    generator = torch.Generator(device="cuda").manual_seed(seed)

    result = pipe(
        image=source,
        prompt=prompt,
        generator=generator,
        num_frames=NUM_FRAMES,
        num_inference_steps=NUM_INFERENCE_STEPS,
        guidance_scale=GUIDANCE,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"diza_{uuid.uuid4().hex[:12]}.mp4")
    export_to_video(result.frames[0], path, fps=FPS)
    return path, f"{NUM_FRAMES} frames · {FPS} fps · target {NUM_FRAMES/FPS:.2f}s · seed {seed}"


with gr.Blocks(title="Diza Hunyuan 5s") as demo:
    gr.Markdown("# Diza Hunyuan 5s")
    with gr.Row():
        with gr.Column():
            image = gr.Image(type="pil", label="Input image")
            prompt = gr.Textbox(lines=5, label="Motion prompt")
            seed = gr.Number(value=-1, precision=0, label="Seed (-1 random)")
            button = gr.Button("Generate 5s", variant="primary")
        with gr.Column():
            video = gr.Video(label="121-frame MP4")
            meta = gr.Textbox(label="Metadata", interactive=False)
    button.click(generate, [image, prompt, seed], [video, meta], api_name="generate")

demo.queue(default_concurrency_limit=1).launch()
