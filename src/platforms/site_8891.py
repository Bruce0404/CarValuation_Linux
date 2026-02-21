import asyncio
import re
import random
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from src.platforms.base import BaseCrawler
from src.models.car import CarListing
from src.core.cleaning import clean_car_data # 導入新的主清洗函數

class Crawler8891(BaseCrawler):
    """
    針對 8891 網站的爬蟲實現。
    繼承自 BaseCrawler，專門負責從 8891 抓取、解析車輛列表。
    """
    
    BASE_URL = "https://auto.8891.com.tw/usedauto-index.html"
    SOURCE_NAME = "site_8891"

    async def fetch_listings(self, page_num: int = 1) -> List[CarListing]:
        """
        抓取指定頁數的車輛列表。
        @param page_num: 要抓取的頁碼。
        @return: 一個包含 CarListing 對象的列表。
        """
        results = []
        target_url = f"{self.BASE_URL}?page={page_num}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(locale="zh-TW")
            page = await context.new_page()

            try:
                self.logger.info(f"正在導航至 8891 第 {page_num} 頁: {target_url}")
                await page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
                await asyncio.sleep(random.uniform(2, 4)) # 模擬人類延遲

                # 等待車輛列表的容器出現
                list_container_selector = 'div[class*="main-list-container"]'
                await page.wait_for_selector(list_container_selector, timeout=20000)

                # 找到所有的車輛項目
                item_selector = 'a[class*="_row-item"]'
                items = await page.query_selector_all(item_selector)
                self.logger.info(f"在頁面 {page_num} 上找到 {len(items)} 筆車輛資料，開始解析...")

                for item in items:
                    try:
                        # 1. 抓取最基礎的原始數據
                        raw_title_element = await item.query_selector('span[class*="_ib-it-text"]')
                        original_title = await raw_title_element.inner_text() if raw_title_element else "無標題"
                        
                        link_href = await item.get_attribute("href") or ""
                        full_link = f"https://auto.8891.com.tw{link_href}" if link_href.startswith("/") else link_href
                        
                        external_id = (link_href.split("id=")[-1] if "id=" in link_href else 
                                       f"fallback_{random.randint(10000, 99999)}")

                        year_text = await item.inner_text()
                        year_match = re.search(r'(20\d{2})', year_text)
                        year = int(year_match.group(1)) if year_match else 2000

                        price_element = await item.query_selector('span[class*="_ib-price"]')
                        price_raw = await price_element.inner_text() if price_element else "0"

                        info_elements = await item.query_selector_all('span[class*="_ib-ii-item"]')
                        location = await info_elements[0].inner_text() if len(info_elements) > 0 else "未知"
                        mileage_raw = await info_elements[1].inner_text() if len(info_elements) > 1 else "0"
                        
                        # 2. 組裝原始數據字典，準備清洗
                        raw_data_for_cleaning = {
                            "original_title": original_title,
                            "price": price_raw,
                            "mileage": mileage_raw,
                        }

                        # 3. 調用核心清洗函數
                        cleaned_data = clean_car_data(raw_data_for_cleaning)

                        # 4. 合併所有數據並實例化 Pydantic 模型
                        final_data = {
                            "source": self.SOURCE_NAME,
                            "external_id": external_id,
                            "link": full_link,
                            "year": year,
                            "location": location.strip(),
                            "original_title": original_title, # 保存原始標題
                            **cleaned_data # 合併清洗後的所有欄位
                        }
                        
                        car_listing = CarListing(**final_data)
                        results.append(car_listing)

                    except Exception as e:
                        self.logger.error(f"解析單筆 8891 車輛數據時出錯: {e}")
                        # 繼續處理下一筆，而不是中斷整個過程
                        continue
            
            finally:
                await browser.close()
                
        self.logger.info(f"完成頁面 {page_num} 的抓取，共獲得 {len(results)} 筆有效數據。")
        return results