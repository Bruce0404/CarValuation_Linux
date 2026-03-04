import asyncio
from playwright.async_api import async_playwright
import re

async def run_test(url):
    # 要阻擋的廣告或追蹤服務網域列表
    block_domains = [
        "doubleclick.net",
        "googlesyndication.com",
        "google-analytics.com",
        "googleadservices.com"
    ]
    # 將列表轉換為正規表達式，用於匹配 URL
    block_regex = re.compile(f"({'|'.join(block_domains)})")

    async with async_playwright() as p:
        # 1. 啟動瀏覽器
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        
        # 2. 建立瀏覽器上下文
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True
        )
        
        page = await context.new_page()

        # 3. 設定請求路由，攔截並阻擋指定的網域
        # 這會讓 Playwright 對所有符合 block_regex 的 URL 直接說「不」，連請求都不會發出去
        await page.route(block_regex, lambda route: route.abort())

        try:
            print(f"正在連線至: {url} (已啟用廣告阻擋)...")
            # 使用 networkidle 確保網頁主要資源加載完成
            response = await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if response:
                print(f"HTTP 狀態碼: {response.status}")
            
            # 4. 截圖保存
            await page.screenshot(path="debug_linux_test.png")
            print("截圖已完成：debug_linux_test.png")
            
            # 5. 檢查頁面標題
            title = await page.title()
            print(f"網頁標題: {title}")

        except Exception as e:
            print(f"發生異常: {e}")
        
        finally:
            await browser.close()

# 執行測試
asyncio.run(run_test("https://auto.8891.com.tw/"))