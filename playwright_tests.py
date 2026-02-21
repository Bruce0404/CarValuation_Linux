import asyncio
from playwright.async_api import async_playwright

async def run_test(url):
    async with async_playwright() as p:
        # 1. 啟動瀏覽器（Linux 環境通常需要 --no-sandbox）
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        
        # 2. 模擬 Windows 環境的 User-Agent，避免被視為機器人
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True  # 忽略 Linux 上嚴格的 SSL 檢查
        )
        
        page = await context.new_page()

        # 3. 監聽網路請求失敗的原因 (Debug 核心)
        page.on("requestfailed", lambda request: print(f">> 請求失敗: {request.url} | 原因: {request.failure}"))

        try:
            print(f"正在連線至: {url} ...")
            # 使用 networkidle 確保網頁完全加載
            response = await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if response:
                print(f"HTTP 狀態碼: {response.status}")
            
            # 4. 截圖保存，方便確認畫面
            await page.screenshot(path="debug_linux_test.png")
            print("截圖已完成：debug_linux_test.png")
            
            # 5. 檢查頁面標題，確認是否真的進入目標網頁
            title = await page.title()
            print(f"網頁標題: {title}")

        except Exception as e:
            print(f"發生異常: {e}")
        
        finally:
            await browser.close()

# 請替換成你要爬的中古車網址或目標 URL
asyncio.run(run_test("https://auto.8891.com.tw/"))