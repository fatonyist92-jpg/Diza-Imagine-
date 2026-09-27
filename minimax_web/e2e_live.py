from playwright.sync_api import sync_playwright
URL="https://cdn.jsdelivr.net/gh/fatonyist92-jpg/Diza-Imagine-@34ff1ba925aae0c972c1780c340064436d9e598b/minimax_web/index.html?selftest=1"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    errors=[]
    page.on("console", lambda m: print("CONSOLE",m.type,m.text,flush=True))
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    print("TITLE",page.title(),flush=True)
    page.wait_for_function("document.getElementById('status').textContent.includes('Video selesai')", timeout=210000)
    status=page.locator("#status").inner_text()
    src=page.locator("#video").get_attribute("src")
    print("FINAL_STATUS",status,flush=True)
    print("VIDEO_SRC",src,flush=True)
    if "Video selesai" not in status or not src or not src.startswith("blob:"):
        raise RuntimeError("Live web did not produce playable blob video")
    if errors:
        print("PAGE_ERRORS",errors,flush=True)
    browser.close()
