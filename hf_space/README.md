---
title: Diza Hunyuan 5s
emoji: 🎬
colorFrom: gray
colorTo: indigo
sdk: gradio
python_version: 3.10.13
sdk_version: 5.49.1
app_file: app.py
pinned: false
models:
  - hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_i2v_step_distilled
tags:
  - zerogpu
  - image-to-video
  - hunyuanvideo
preload_from_hub:
  - hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_i2v_step_distilled
startup_duration_timeout: 1h
---

# Diza Hunyuan 5s

Private backend recipe for Diza Imagine.

- HunyuanVideo 1.5 480p I2V Step-Distilled
- 121 generated frames
- 24 fps
- 4 inference steps
- raw prompt pass-through
- no prompt rewrite
- ZeroGPU
