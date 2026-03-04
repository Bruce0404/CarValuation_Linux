import asyncio
import re
import random
from typing import List
from loguru import logger
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from src.platforms.base import BaseCrawler
from src.models.car import CarListing
from src.core.cleaning import clean_car_data

class ListContainerNotFound(Exception):
    """當在頁面中找不到列表容器時拋出此異常。"""
    pass

class Crawler8891(BaseCrawler):
    """
    針對 8891 網站的爬蟲實現（使用 Playwright）。
    """
    
    BASE_URL = "https://auto.8891.com.tw/usedauto-index.html"
    SOURCE_NAME = "site_8891"

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.browser = None
        self.context = None

    async def launch_browser(self):
        """啟動 Playwright 瀏覽器實例。"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        logger.info("Playwright 瀏覽器已啟動。")

    async def close_browser(self):
        """關閉 Playwright 瀏覽器實例。"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Playwright 瀏覽器已關閉。")

    async def fetch_listings(self, page_num: int = 1) -> List[CarListing]:
        """
        使用 Playwright 抓取指定頁數的車輛列表。
        @param page_num: 要抓取的頁碼。
        @return: 一個包含 CarListing 對象的列表。
        """
        if not self.browser or not self.context:
            await self.launch_browser()

        page = await self.context.new_page()
        results = []
        url = f"{self.BASE_URL}?page={page_num}"

        try:
            logger.info(f"正在導航至 8891 第 {page_num} 頁: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            logger.info("頁面初次加載完成，等待5秒觀察穩定情況...")
            await page.wait_for_timeout(5000)

            # 最終嘗試：尋找是否存在任何形式的遮罩層或驗證碼
            # Cloudflare Turnstile CAPTCHA 的典型選擇器
            captcha_selector = 'iframe[src*="challenges.cloudflare.com"]'
            try:
                await page.wait_for_selector(captcha_selector, timeout=5000)
                logger.error("檢測到 Cloudflare CAPTCHA，無法自動處理。這是爬蟲失敗的根本原因。")
                raise ListContainerNotFound("檢測到 CAPTCHA，腳本終止。")
            except PlaywrightTimeoutError:
                logger.info("未檢測到 Cloudflare CAPTCHA。")

            # 如果沒有 CAPTCHA，再最後一次嘗試尋找列表容器
            list_container_selector = "div[class*='main-list-container']"
            try:
                logger.info(f"正在最後一次嘗試尋找列表容器: {list_container_selector}")
                await page.wait_for_selector(list_container_selector, timeout=10000)
            except PlaywrightTimeoutError:
                screenshot_path = "final_attempt_failure.png"
                await page.screenshot(path=screenshot_path)
                html_content = await page.content()
                with open("final_attempt_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.error(f"最終嘗試失敗，仍未找到列表容器。截圖和HTML已保存，請檢查。")
                raise ListContainerNotFound(f"在頁面 {page_num} 上找不到車輛列表容器。")

            # 找到所有的車輛項目
            item_selector = "a[class*='_row-item']"
            items = await page.query_selector_all(item_selector)
            logger.info(f"在頁面 {page_num} 上找到 {len(items)} 筆車輛資料，開始解析...")

            for item_handle in items:
                try:
                    title_element = await item_handle.query_selector('span[class*="_ib-it-text"]')
                    original_title = await title_element.inner_text() if title_element else "無標題"
                    link_href = await item_handle.get_attribute("href") or ""
                    full_link = f"https://auto.8891.com.tw{link_href}" if link_href.startswith("/") else link_href
                    id_match = re.search(r'-(\d+)', link_href)
                    external_id = id_match.group(1) if id_match else f"fallback_{random.randint(10000, 99999)}"
                    item_text = await item_handle.inner_text()
                    year_match = re.search(r'(20\d{2})', item_text)
                    year = int(year_match.group(1)) if year_match else 2000
                    price_element = await item_handle.query_selector('span[class*="_ib-price"]')
                    price_raw = await price_element.inner_text() if price_element else "0"
                    info_elements = await item_handle.query_selector_all('span[class*="_ib-ii-item"]')
                    location = await info_elements[0].inner_text() if len(info_elements) > 0 else "未知"
                    mileage_raw = await info_elements[1].inner_text() if len(info_elements) > 1 else "0"
                    
                    raw_data_for_cleaning = {"original_title": original_title, "price": price_raw, "mileage": mileage_raw}
                    cleaned_data = clean_car_data(raw_data_for_cleaning)

                    car_listing = CarListing(
                        source_platform=self.SOURCE_NAME,
                        external_id=external_id,
                        link=full_link,
                        brand=cleaned_data['brand'],
                        series=cleaned_data['series'],
                        year=year,
                        price_wan=cleaned_data['price'],
                        mileage_wan=cleaned_data['mileage'],
                        original_name=original_title,
                        model_name=cleaned_data['processed_title'],
                    )
                    results.append(car_listing)
                except Exception as e:
                    logger.error(f"解析單筆 8891 車輛數據時出錯: {e}")
                    continue
        
        except Exception as e:
            logger.opt(exception=True).error(f"抓取 8891 頁面 {page_num} 時發生未預期的錯誤: {e}")
            screenshot_path = "error_screenshot.png"
            try:
                await page.screenshot(path=screenshot_path)
                logger.error(f"已截圖至 {screenshot_path}，請檢查圖片以了解當前頁面狀況。")
            except Exception as screenshot_error:
                logger.error(f"截圖失敗: {screenshot_error}")
            raise
        
        finally:
            await page.close()
            
        logger.info(f"完成頁面 {page_num} 的抓取，共獲得 {len(results)} 筆有效數據。")
        return results

async def main():
    """調試用的異步函數"""
    crawler = Crawler8891(headless=True)
    try:
        await crawler.launch_browser()
        listings = await crawler.fetch_listings(page_num=1)
        if listings:
            logger.success(f"成功抓取到 {len(listings)} 筆數據。")
        else:
            logger.warning("未抓取到任何數據。")
    except Exception as e:
        logger.error(f"調試過程中發生錯誤: {e}")
    finally:
        await crawler.close_browser()

if __name__ == "__main__":
    asyncio.run(main())
