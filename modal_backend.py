import io
import os
import tempfile

import modal

MODEL_ID = "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_i2v_step_distilled"
NUM_FRAMES = 121
FPS = 24
NUM_STEPS = 12

app = modal.App("diza-hunyuan-i2v")
volume = modal.Volume.from_name("diza-hunyuan-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch",
        "diffusers",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "pillow",
        "fastapi[standard]",
        "imageio-ffmpeg",
    )
)

@app.cls(
    image=image,
    gpu="A10G",
    timeout=1800,
    scaledown_window=120,
    volumes={"/cache": volume},
)
class HunyuanI2V:
    @modal.enter()
    def load(self):
        import torch
        from diffusers import HunyuanVideo15ImageToVideoPipeline

        os.environ["HF_HOME"] = "/cache/huggingface"
        self.torch = torch
        self.pipe = HunyuanVideo15ImageToVideoPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )
        self.pipe.enable_model_cpu_offload()
        self.pipe.vae.enable_tiling()
        self.pipe.vae.enable_slicing()

    @modal.fastapi_endpoint(method="POST", docs=True)
    async def generate(self, request):
        import imageio_ffmpeg
        from diffusers.utils import export_to_video
        from fastapi import HTTPException
        from PIL import Image

        form = await request.form()
        upload = form.get("image")
        prompt = str(form.get("prompt") or "").strip()
        seed_raw = form.get("seed", "-1")
        if upload is None:
            raise HTTPException(400, "Image kosong.")
        if not prompt:
            raise HTTPException(400, "Prompt kosong.")

        seed = int(seed_raw)
        if seed < 0:
            seed = int.from_bytes(os.urandom(4), "big") & 0x7FFFFFFF

        raw = await upload.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")

        self.torch.cuda.empty_cache()
        frames = self.pipe(
            image=img,
            prompt=prompt,
            generator=self.torch.Generator(device="cpu").manual_seed(seed),
            num_frames=NUM_FRAMES,
            num_inference_steps=NUM_STEPS,
        ).frames[0]

        if len(frames) != NUM_FRAMES:
            raise HTTPException(500, f"Frame output salah: {len(frames)} / {NUM_FRAMES}")

        path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        export_to_video(frames, path, fps=FPS)
        n, sec = imageio_ffmpeg.count_frames_and_secs(path)
        if sec < 4.5:
            raise HTTPException(500, f"Durasi output salah: {sec:.3f}s")

        from fastapi.responses import FileResponse
        return FileResponse(
            path,
            media_type="video/mp4",
            filename=f"diza_hunyuan_{seed}.mp4",
            headers={"X-Diza-Frames": str(n), "X-Diza-Duration": f"{sec:.3f}", "X-Diza-Seed": str(seed)},
        )
