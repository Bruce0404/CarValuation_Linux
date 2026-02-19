import asyncio
import re
import random
import unicodedata
from typing import List
from playwright.async_api import async_playwright
from src.platforms.base import BaseCrawler 
from src.models.car import CarListing

# 更加強健的正則表達式
RE_PRICE = re.compile(r'([\d,]+\.?\d*)')
RE_YEAR = re.compile(r'(19\d{2}|20\d{2})') # 匹配 19xx 或 20xx

class Crawler8891(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        
    BASE_URL = "https://auto.8891.com.tw/usedauto-index.html"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    async def fetch_listings(self, page: int = 1) -> List[CarListing]:
        results = []
        target_url = f"{self.BASE_URL}?page={page}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"]
            )

            context = await browser.new_context(
                user_agent=random.choice(self.USER_AGENTS),
                viewport={'width': 1280, 'height': 800},
                locale="zh-TW"
            )
            
            page_obj = await context.new_page()

            # 暴力掃除任何可能擋住點擊的元素
            await page_obj.add_init_script("""
                setInterval(() => {
                    const overlays = document.querySelectorAll('.el-overlay, .v-modal, [id*="auth-modal"], .el-message-box__wrapper');
                    overlays.forEach(el => el.remove());
                    document.body.style.overflow = 'auto';
                }, 500);
            """)

            try:
                self.logger.info(f"正在連線至 {target_url}...")
                await page_obj.goto(target_url, wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(2)

                # 使用模糊匹配動態 Class 
                item_selector = 'a[class*="_row-item"]' # 8891 最外層的 A 標籤
                
                try:
                    await page_obj.wait_for_selector(item_selector, timeout=15000, state="attached")
                except:
                    self.logger.error("無法定位車輛 A 標籤，請檢查網站結構是否變更")
                    return []

                # 捲動加載
                await page_obj.evaluate("window.scrollBy(0, 1000);")
                await asyncio.sleep(1)

                items = await page_obj.query_selector_all(item_selector)
                self.logger.info(f"--- 偵測到 {len(items)} 個原始區塊，開始解析 Pydantic 模型 ---")
                
                for item in items:
                    try:
                        href = await item.get_attribute("href")
                        if not href: continue
                        
                        full_text = await item.inner_text()
                        
                        # 1. 標題與 ID
                        title_el = await item.query_selector('span[class*="_ib-it-text"]')
                        title = (await title_el.inner_text()).strip() if title_el else "未知車款"
                        ext_id = href.split("id=")[-1].split("&")[0] if "id=" in href else str(random.randint(10000, 99999))
                        
                        # 2. 價格解析
                        price_el = await item.query_selector('span[class*="_ib-price"]')
                        price_raw = await price_el.inner_text() if price_el else "0"
                        price_match = RE_PRICE.search(price_raw)
                        price_val = float(price_match.group(1).replace(',', '')) if price_match else 0.0

                        # 3. 年份解析 (從全文本中找 20xx)
                        year_match = RE_YEAR.search(full_text)
                        year_val = int(year_match.group(1)) if year_match else 2020
                        
                        # 4. 地區與里程解析
                        info_items = await item.query_selector_all('span[class*="_ib-ii-item"]')
                        location = "全台"
                        mileage_raw = "0"
                        if len(info_items) > 0:
                            location = (await info_items[0].inner_text()).strip()
                        if len(info_items) > 1:
                            mileage_raw = (await info_items[1].inner_text()).strip()

                        # 建立物件
                        car = CarListing(
                            source="8891",
                            external_id=ext_id,
                            title=title,
                            year=max(1990, min(2026, year_val)), 
                            price=price_val,
                            mileage=mileage_raw, # Pass raw string to the model for validation
                            location=location[:3], # 取前三個字如「桃園市」
                            link=f"https://auto.8891.com.tw{href}" if href.startswith("/") else href
                        )
                        results.append(car)
                    except Exception as e:
                        # 如果某筆失敗，印出原因以便修正模型定義
                        self.logger.debug(f"單筆模型驗證失敗: {e}")
                        continue
            finally:
                await browser.close()
        return results