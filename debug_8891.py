import asyncio
import re
import random
import unicodedata
import os
from typing import List
from playwright.async_api import async_playwright
from src.platforms.base import 
from src.models.car import CarListing

# Regex 規則 (解析價格與年份)
RE_PRICE = re.compile(r'([\d,]+\.?\d*)\s*萬(?!\s*公里)')
RE_YEAR = re.compile(r'(20\d{2})')

class Crawler8891():
    BASE_URL = "https://auto.8891.com.tw/usedauto-index.html"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    async def fetch_listings(self, page: int = 1) -> List[CarListing]:
        results = []
        target_url = f"{self.BASE_URL}?page={page}"
        
        async with async_playwright() as p:
            self.logger.info("--- [Debug模式] 啟動瀏覽器 ---")
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )

            context = await browser.new_context(
                user_agent=random.choice(self.USER_AGENTS),
                viewport={'width': 1280, 'height': 800},
                locale="zh-TW",
                permissions=[] 
            )
            
            page_obj = await context.new_page()

            # 注入強力背景腳本：每 100ms 穿透彈窗一次
            await page_obj.add_init_script("""
                setInterval(() => {
                    const overlays = document.querySelectorAll('.el-message-box__wrapper, .v-modal, .el-dialog__wrapper, .el-overlay, [class*="modal"], [class*="overlay"]');
                    overlays.forEach(el => {
                        el.style.pointerEvents = 'none';
                        el.style.opacity = '0.1'; // 設為極淡，以便 debug 截圖能看穿
                        el.style.zIndex = '-9999'; 
                    });
                    document.body.style.setProperty('overflow', 'auto', 'important');
                    document.documentElement.style.setProperty('overflow', 'auto', 'important');
                }, 100);
            """)

            try:
                self.logger.info(f"正在連線至: {target_url}")
                await page_obj.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                
                # 第一階段截圖：剛進入頁面
                await asyncio.sleep(2)
                await page_obj.screenshot(path="debug_step1_initial.png")
                self.logger.info("已完成 Step 1 截圖: 初始載入")

                # 第二階段：確認 DOM 中是否有 .ib-item
                html_content = await page_obj.content()
                item_count_in_html = html_content.count('class="ib-item"')
                self.logger.info(f"Step 2: HTML 源碼偵測到 {item_count_in_html} 個 'ib-item' 標籤")

                # 保存 HTML 供手動分析
                with open("debug_page_source.html", "w", encoding="utf-8") as f:
                    f.write(html_content)

                # 嘗試等待元素 (attached 狀態，不論是否被擋住)
                try:
                    await page_obj.wait_for_selector(".ib-item", timeout=15000, state="attached")
                    self.logger.info("Step 3: 成功定位到車輛列表節點 (Attached)")
                except Exception as e:
                    self.logger.error(f"Step 3 失敗: 無法在 DOM 中找到車輛列表。錯誤: {e}")
                    await page_obj.screenshot(path="debug_step3_failed.png")
                    return []

                # 第三階段：執行捲動並解析
                await page_obj.evaluate("window.scrollBy(0, 1000);")
                await asyncio.sleep(2)
                await page_obj.screenshot(path="debug_step4_after_scroll.png")

                items = await page_obj.query_selector_all(".ib-item")
                self.logger.info(f"--- 最終解析: 偵測到 {len(items)} 筆車輛資料 ---")
                
                for i, item in enumerate(items):
                    try:
                        link_el = await item.query_selector(".ib-tit a") or await item.query_selector("a")
                        if not link_el: continue
                        
                        title = (await link_el.inner_text()).strip()
                        href = await link_el.get_attribute("href")
                        
                        # 擷取價格
                        full_text = await item.inner_text()
                        price_match = RE_PRICE.search(full_text)
                        price_val = float(price_match.group(1).replace(',', '')) if price_match else 0.0

                        if i < 3: # 只記錄前三筆做 debug
                            self.logger.debug(f"抓取測試 [{i}]: {title} | 價格: {price_val}")

                        results.append(CarListing(
                            source="8891",
                            external_id=href.split("id=")[-1] if "id=" in href else str(random.randint(1,999)),
                            title=title,
                            year=2020, 
                            price=price_val,
                            mileage=0.0,
                            location="全台",
                            link=f"https://auto.8891.com.tw{href}" if href.startswith("/") else href
                        ))
                    except Exception as e:
                        self.logger.error(f"解析第 {i} 筆資料出錯: {e}")
                        continue
            finally:
                await browser.close()
                self.logger.info("--- Debug 任務結束，瀏覽器已關閉 ---")
        
        return results