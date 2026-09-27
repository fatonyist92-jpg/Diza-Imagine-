from playwright.sync_api import sync_playwright
from urllib.request import urlretrieve

URL="https://fatonyist92-jpg.github.io/Diza-Imagine-/minimax_web/"
IMG="/tmp/bus.png"
urlretrieve("https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png", IMG)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.on("console", lambda m: print("CONSOLE",m.type,m.text,flush=True))
    page.on("pageerror", lambda e: print("PAGEERROR",e,flush=True))
    page.goto(URL, wait_until="networkidle", timeout=60000)
    print("TITLE",page.title(),flush=True)
    page.set_input_files("#image", IMG)
    page.fill("#prompt", "The bus moves slowly forward while the camera remains stationary.")
    page.click("#go")
    page.wait_for_function("document.getElementById('status').textContent.includes('Video selesai')", timeout=240000)
    status=page.locator("#status").inner_text()
    src=page.locator("#video").get_attribute("src")
    page.wait_for_function("document.getElementById('video').readyState >= 2", timeout=30000)
    ready=page.locator("#video").evaluate("(v)=>({readyState:v.readyState,duration:v.duration,videoWidth:v.videoWidth,videoHeight:v.videoHeight})")
    print("FINAL_STATUS",status,flush=True)
    print("VIDEO_SRC",src,flush=True)
    print("VIDEO_READY",ready,flush=True)
    if "Video selesai" not in status or not src or not src.startswith("blob:") or ready["duration"] < 9:
        raise RuntimeError("Public live web did not return a valid generated video")
    browser.close()
