import os, shutil, tempfile
from flask import Flask, request, send_file, render_template_string, jsonify
from gradio_client import Client, handle_file

app=Flask(__name__)
HTML=r'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diza Imagine</title><style>
*{box-sizing:border-box}body{margin:0;background:#070707;color:#f5f5f5;font-family:Inter,system-ui,sans-serif}main{max-width:760px;margin:auto;padding:28px 18px 60px}.brand{font-weight:750;font-size:20px;letter-spacing:-.4px;margin-bottom:28px}.panel{border:1px solid #242424;background:#0d0d0d;border-radius:18px;padding:16px}.drop{height:290px;border:1px dashed #383838;border-radius:14px;display:grid;place-items:center;overflow:hidden;background:#111;cursor:pointer}.drop img{width:100%;height:100%;object-fit:contain}.muted{color:#888;font-size:13px}textarea{width:100%;min-height:120px;margin-top:14px;background:#111;border:1px solid #2b2b2b;border-radius:14px;color:#fff;padding:14px;font:inherit;resize:vertical;outline:none}button{width:100%;height:52px;border:0;border-radius:14px;margin-top:12px;background:#fff;color:#050505;font-weight:750;font-size:15px;cursor:pointer}button:disabled{opacity:.45}.status{min-height:22px;margin:14px 2px 0;color:#aaa;font-size:13px}.result{margin-top:16px}.result video{width:100%;border-radius:14px;background:#000;max-height:70vh}.row{display:flex;justify-content:space-between;align-items:center;margin-top:10px}.pill{font-size:11px;color:#aaa;border:1px solid #292929;border-radius:99px;padding:5px 8px}
</style></head><body><main><div class="brand">DIZA IMAGINE <span class="pill">HunyuanVideo 1.5</span></div><div class="panel">
<label class="drop" id="drop"><span id="hint"><b>Upload image</b><br><span class="muted">JPG / PNG / WEBP</span></span><img id="preview" hidden></label><input id="file" type="file" accept="image/*" hidden>
<textarea id="prompt" placeholder="Describe the motion..."></textarea><button id="go">Generate video</button><div class="status" id="status"></div><div class="result" id="result"></div>
</div></main><script>
const file=document.querySelector('#file'),drop=document.querySelector('#drop'),preview=document.querySelector('#preview'),hint=document.querySelector('#hint'),go=document.querySelector('#go'),status=document.querySelector('#status'),result=document.querySelector('#result');
drop.onclick=()=>file.click();file.onchange=()=>{if(!file.files[0])return;preview.src=URL.createObjectURL(file.files[0]);preview.hidden=false;hint.hidden=true}
go.onclick=async()=>{if(!file.files[0]||!document.querySelector('#prompt').value.trim()){status.textContent='Upload image dan isi prompt dulu.';return}go.disabled=true;result.innerHTML='';status.textContent='Generating with Hunyuan...';let fd=new FormData();fd.append('image',file.files[0]);fd.append('prompt',document.querySelector('#prompt').value);
try{let r=await fetch('/generate',{method:'POST',body:fd});if(!r.ok){let t=await r.text();throw Error(t)}let b=await r.blob();let u=URL.createObjectURL(b);result.innerHTML='<video controls autoplay loop playsinline src="'+u+'"></video><div class="row"><span class="muted">MP4 ready</span><a id="dl" class="pill" style="color:#fff;text-decoration:none" download="hunyuan.mp4" href="'+u+'">Download MP4</a></div>';status.textContent='Done ✓'}catch(e){status.textContent='Generation failed: '+e.message.slice(0,180)}finally{go.disabled=false}}
</script></body></html>'''

@app.get("/")
def index(): return render_template_string(HTML)

@app.get("/health")
def health(): return {"ok":True,"engine":"HunyuanVideo-1.5"}

@app.post("/generate")
def generate():
    if "image" not in request.files: return "image required",400
    prompt=(request.form.get("prompt") or "").strip()
    if not prompt: return "prompt required",400
    td=tempfile.mkdtemp(prefix="hunyuan_")
    inp=os.path.join(td,"input.png"); request.files["image"].save(inp)
    try:
        token=os.environ.get("HF_TOKEN") or None
        client=Client("multimodalart/Hunyuan-Video-1-5", token=token)
        result=client.predict(handle_file(inp),prompt,17,2,5.0,1,1.0,False,fn_index=0)
        def path(x):
            if isinstance(x,str) and os.path.exists(x): return x
            if isinstance(x,dict):
                for v in x.values():
                    p=path(v)
                    if p:return p
            if isinstance(x,(list,tuple)):
                for v in x:
                    p=path(v)
                    if p:return p
        p=path(result)
        if not p: return "Hunyuan returned no video",502
        out=os.path.join(td,"result.mp4"); shutil.copy2(p,out)
        return send_file(out,mimetype="video/mp4",as_attachment=False,download_name="hunyuan.mp4")
    except Exception as e:
        return str(e),502

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
