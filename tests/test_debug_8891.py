import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# This is a bit of a hack, because the file is not in a package
# we need to add the parent directory to the path to import from it
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.platforms.site_8891 import Crawler8891
from src.models.car import CarListing

class TestCrawler8891(unittest.IsolatedAsyncioTestCase):

    @patch('src.platforms.site_8891.clean_car_data')
    @patch('src.platforms.site_8891.async_playwright')
    async def test_fetch_listings_success(self, mock_async_playwright, mock_clean_car_data):
        """
        測試 fetch_listings 在成功抓取網頁資料時的行為
        """
        # --- Mock Setup ---
        
        # 1. 模擬清洗函數的返回值
        mock_clean_car_data.side_effect = [
            {
                "brand": "測試品牌一", "series": "測試車系一", "price": 88.8, 
                "mileage": 1.0, "processed_title": "處理後標題一"
            },
            {
                "brand": "測試品牌二", "series": "測試車系二", "price": 102.0,
                "mileage": 2.0, "processed_title": "處理後標題二"
            }
        ]

        # 2. 創建 Playwright 主要物件的模擬
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # 設定 context manager 的回傳值
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # 3. 模擬網頁元素
        mock_item1 = AsyncMock()
        mock_item2 = AsyncMock()

        # 模擬第一個元素的內容
        raw_title_element1 = AsyncMock()
        raw_title_element1.inner_text.return_value = "原始標題一"
        mock_item1.get_attribute.return_value = "/usedauto-infos-12345.html"
        mock_item1.query_selector.return_value = raw_title_element1
        mock_item1.inner_text.return_value = "一些包含 2021 年的文字" # 用於年份解析

        # 模擬第二個元素的內容
        raw_title_element2 = AsyncMock()
        raw_title_element2.inner_text.return_value = "原始標題二"
        mock_item2.get_attribute.return_value = "https://auto.8891.com.tw/usedauto-infos-67890.html"
        mock_item2.query_selector.return_value = raw_title_element2
        mock_item2.inner_text.return_value = "一些包含 2022 年的文字" # 用於年份解析
        
        mock_page.query_selector_all.return_value = [mock_item1, mock_item2]
        
        # --- Test Execution ---
        crawler = Crawler8891(headless=True)
        results = await crawler.fetch_listings(page_num=1)

        # --- Assertions ---
        # 驗證抓取和解析邏輯
        self.assertEqual(len(results), 2)

        # 驗證第一筆資料的內容
        car1 = results[0]
        self.assertIsInstance(car1, CarListing)
        self.assertEqual(car1.original_name, "原始標題一")
        self.assertEqual(car1.brand, "測試品牌一") # 驗證清洗後數據
        self.assertEqual(car1.series, "測試車系一") # 驗證清洗後數據
        self.assertEqual(car1.price_wan, 88.8) # 驗證清洗後數據
        self.assertEqual(car1.year, 2021) # 驗證年份解析
        self.assertEqual(car1.external_id, "12345")
        self.assertEqual(car1.link, "https://auto.8891.com.tw/usedauto-infos-12345.html")
        self.assertEqual(car1.source_platform, "site_8891")

        # 驗證第二筆資料的內容
        car2 = results[1]
        self.assertEqual(car2.original_name, "原始標題二")
        self.assertEqual(car2.brand, "測試品牌二")
        self.assertEqual(car2.price_wan, 102.0)
        self.assertEqual(car2.year, 2022)
        self.assertEqual(car2.external_id, "67890")
        self.assertEqual(car2.link, "https://auto.8891.com.tw/usedauto-infos-67890.html")


if __name__ == '__main__':
    unittest.main()
