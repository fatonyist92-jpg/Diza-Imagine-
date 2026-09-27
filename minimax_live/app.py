from flask import Flask, request, send_file, jsonify, render_template_string
from gradio_client import Client, handle_file
from PIL import Image
import tempfile, os, shutil, threading, time

app = Flask(__name__)
SPACE = "MiniMaxAI/MiniMax-H3-Turbo-Lora"
_client = None
_lock = threading.Lock()

def get_client():
    global _client
    with _lock:
        if _client is None:
            _client = Client(SPACE, verbose=False)
        return _client

HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DIZA Imagine · MiniMax H3</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#050505;color:#f5f5f5;font-family:Inter,system-ui,-apple-system,sans-serif}
.wrap{max-width:760px;margin:auto;padding:22px 16px 56px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}
.brand{font-weight:800;letter-spacing:-.04em;font-size:23px}.engine{font-size:12px;color:#aaa;border:1px solid #2b2b2b;padding:7px 10px;border-radius:999px}
.card{border:1px solid #222;background:#0b0b0b;border-radius:18px;padding:14px;margin-bottom:12px}
.drop{min-height:270px;border:1px dashed #353535;border-radius:14px;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative;background:#080808;cursor:pointer}
.drop img{width:100%;height:100%;max-height:440px;object-fit:contain}.drop input{position:absolute;inset:0;opacity:0;cursor:pointer}.hint{text-align:center;color:#999}.hint b{color:#eee}
textarea{width:100%;min-height:120px;resize:vertical;background:#080808;border:1px solid #292929;border-radius:14px;color:#fff;padding:14px;font:inherit;outline:none}
textarea:focus{border-color:#555}.row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.pill{border:1px solid #303030;background:#111;color:#ddd;padding:9px 12px;border-radius:999px;font-size:13px}.pill.on{background:#eee;color:#050505;border-color:#eee}
button{width:100%;margin-top:12px;border:0;border-radius:14px;padding:15px;background:#f2f2f2;color:#050505;font-size:15px;font-weight:800;cursor:pointer}button:disabled{opacity:.45;cursor:not-allowed}
.progress{height:4px;background:#202020;border-radius:99px;overflow:hidden;margin-top:13px;display:none}.bar{height:100%;width:0;background:#eee;transition:width .5s}
.status{color:#aaa;font-size:13px;margin-top:9px;min-height:18px}.result{display:none}.result video{width:100%;border-radius:14px;background:#000}.download{display:block;text-align:center;background:#f2f2f2;color:#050505;text-decoration:none;font-weight:800;padding:14px;border-radius:14px;margin-top:10px}
.note{font-size:12px;color:#777;margin-top:9px;line-height:1.5}
</style></head><body><main class="wrap">
<div class="top"><div class="brand">DIZA Imagine</div><div class="engine">MiniMax H3 Turbo</div></div>
<div class="card"><label class="drop" id="drop"><div class="hint" id="hint"><b>Upload image</b><br>Tap untuk pilih foto</div><img id="preview" style="display:none"><input id="image" type="file" accept="image/*"></label></div>
<div class="card"><textarea id="prompt" placeholder="Describe the motion..."></textarea>
<div class="row"><span class="pill on">1:1 · 544p</span><span class="pill on">10 sec</span><span class="pill">4 steps</span></div>
<div class="note">Prompt dikirim persis seperti yang kamu ketik. Prompt upsampling OFF.</div>
<button id="go">GENERATE VIDEO</button><div class="progress" id="prog"><div class="bar" id="bar"></div></div><div class="status" id="status"></div></div>
<div class="card result" id="result"><video id="video" controls playsinline loop></video><a class="download" id="download" download="DIZA-MiniMax-H3.mp4">DOWNLOAD MP4</a></div>
</main><script>
const image=document.getElementById('image'),preview=document.getElementById('preview'),hint=document.getElementById('hint'),go=document.getElementById('go'),status=document.getElementById('status'),prog=document.getElementById('prog'),bar=document.getElementById('bar'),result=document.getElementById('result'),video=document.getElementById('video'),download=document.getElementById('download');
let timer=null,pct=0,lastUrl=null;
image.onchange=()=>{const f=image.files[0];if(!f)return;preview.src=URL.createObjectURL(f);preview.style.display='block';hint.style.display='none'};
go.onclick=async()=>{const f=image.files[0],p=document.getElementById('prompt').value;if(!f||!p.trim()){status.textContent='Image dan prompt wajib diisi.';return}
go.disabled=true;result.style.display='none';prog.style.display='block';pct=5;bar.style.width=pct+'%';status.textContent='Uploading image…';
timer=setInterval(()=>{pct=Math.min(92,pct+(pct<35?4:pct<70?2:1));bar.style.width=pct+'%';status.textContent=pct<25?'Uploading image…':pct<45?'Masuk antrean MiniMax H3…':pct<90?'MiniMax H3 sedang membuat video…':'Finishing MP4…'},1200);
try{const fd=new FormData();fd.append('image',f);fd.append('prompt',p);const r=await fetch('/generate',{method:'POST',body:fd});if(!r.ok){let e='Generate gagal';try{e=(await r.json()).error||e}catch{}throw new Error(e)}
const blob=await r.blob();if(lastUrl)URL.revokeObjectURL(lastUrl);lastUrl=URL.createObjectURL(blob);video.src=lastUrl;download.href=lastUrl;result.style.display='block';pct=100;bar.style.width='100%';status.textContent='Video selesai ✓';video.play().catch(()=>{});
}catch(e){status.textContent=e.message||'Generate gagal.';bar.style.width='0%'}finally{clearInterval(timer);go.disabled=false}}
</script></body></html>'''

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/health")
def health():
    return {"ok": True, "engine": SPACE}

@app.post("/generate")
def generate():
    try:
        f = request.files.get("image")
        prompt = request.form.get("prompt", "")
        if not f or not prompt.strip():
            return jsonify(error="Image dan prompt wajib diisi."), 400

        work = tempfile.mkdtemp(prefix="diza_")
        src = os.path.join(work, "input")
        f.save(src)
        img = Image.open(src).convert("RGB")
        side = min(img.width, img.height)
        left, top = (img.width-side)//2, (img.height-side)//2
        square = os.path.join(work, "input_544.jpg")
        img.crop((left, top, left+side, top+side)).resize((544,544), Image.Resampling.LANCZOS).save(square, quality=95)

        result = get_client().predict(
            prompt,
            handle_file(square),
            None,
            "544x544 · 1:1 fast",
            10,
            4,
            42,
            False,
            "larry",
            api_name="/output_video",
        )
        video_path = result[0]
        if not video_path or not os.path.exists(video_path):
            shutil.rmtree(work, ignore_errors=True)
            return jsonify(error="MiniMax selesai tetapi MP4 tidak ditemukan."), 502

        out = os.path.join(work, "DIZA-MiniMax-H3-10s.mp4")
        shutil.copyfile(video_path, out)
        response = send_file(out, mimetype="video/mp4", as_attachment=False, download_name="DIZA-MiniMax-H3-10s.mp4")
        response.call_on_close(lambda: shutil.rmtree(work, ignore_errors=True))
        return response
    except Exception as e:
        return jsonify(error=str(e)), 502
