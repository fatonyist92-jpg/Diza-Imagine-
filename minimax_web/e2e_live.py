from playwright.sync_api import sync_playwright
URL="http://127.0.0.1:8765/minimax_web/index.html?selftest=1"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.on("console", lambda m: print("CONSOLE",m.type,m.text,flush=True))
    page.on("pageerror", lambda e: print("PAGEERROR",e,flush=True))
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    print("TITLE",page.title(),flush=True)
    page.wait_for_function("document.getElementById('status') && document.getElementById('status').textContent.includes('Video selesai')", timeout=210000)
    status=page.locator("#status").inner_text()
    src=page.locator("#video").get_attribute("src")
    ready=page.locator("#video").evaluate("(v)=>({readyState:v.readyState,duration:v.duration,videoWidth:v.videoWidth,videoHeight:v.videoHeight})")
    print("FINAL_STATUS",status,flush=True)
    print("VIDEO_SRC",src,flush=True)
    print("VIDEO_READY",ready,flush=True)
    if "Video selesai" not in status or not src or not src.startswith("blob:") or ready["duration"] < 9:
        raise RuntimeError("Browser did not receive a valid generated video")
    browser.close()
