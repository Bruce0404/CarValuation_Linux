import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# This is a bit of a hack, because the file is not in a package
# we need to add the parent directory to the path to import from it
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from debug_8891 import Crawler8891, CarListing

class TestCrawler8891(unittest.IsolatedAsyncioTestCase):

    @patch('debug_8891.async_playwright')
    async def test_fetch_listings_success(self, mock_async_playwright):
        """
        測試 fetch_listings 在成功抓取網頁資料時的行為
        """
        # --- Mock Setup ---
        # 創建 Playwright 主要物件的模擬
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # 設定 context manager 的回傳值
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # 模擬網頁元素
        mock_item1 = AsyncMock()
        mock_item2 = AsyncMock()

        # 模擬第一個元素的內容
        mock_link1 = AsyncMock()
        mock_link1.inner_text.return_value = "測試車輛一"
        mock_link1.get_attribute.return_value = "/usedauto-infos-12345.html"
        mock_item1.query_selector.return_value = mock_link1
        mock_item1.inner_text.return_value = "【測試車輛一】 2021年 售價：88.8 萬"

        # 模擬第二個元素的內容
        mock_link2 = AsyncMock()
        mock_link2.inner_text.return_value = "測試車輛二"
        mock_link2.get_attribute.return_value = "https://auto.8891.com.tw/usedauto-infos-67890.html"
        mock_item2.query_selector.return_value = mock_link2
        mock_item2.inner_text.return_value = "【測試車輛二】 2022年 售價：102.0 萬"
        
        mock_page.query_selector_all.return_value = [mock_item1, mock_item2]
        
        # --- Test Execution ---
        crawler = Crawler8891(headless=True)
        results = await crawler.fetch_listings(page=1)

        # --- Assertions ---
        # 驗證啟動瀏覽器的參數
        mock_playwright.chromium.launch.assert_called_once_with(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )

        # 驗證網頁導航
        mock_page.goto.assert_called_once_with("https://auto.8891.com.tw/usedauto-index.html?page=1", wait_until="domcontentloaded", timeout=60000)

        # 驗證解析結果的數量
        self.assertEqual(len(results), 2)

        # 驗證第一筆資料的內容
        car1 = results[0]
        self.assertIsInstance(car1, CarListing)
        self.assertEqual(car1.title, "測試車輛一")
        self.assertEqual(car1.price, 88.8)
        self.assertEqual(car1.external_id, "12345")
        self.assertEqual(car1.link, "https://auto.8891.com.tw/usedauto-infos-12345.html")
        self.assertEqual(car1.source, "8891")

        # 驗證第二筆資料的內容
        car2 = results[1]
        self.assertEqual(car2.title, "測試車輛二")
        self.assertEqual(car2.price, 102.0)
        self.assertEqual(car2.external_id, "67890")
        self.assertEqual(car2.link, "https://auto.8891.com.tw/usedauto-infos-67890.html")


if __name__ == '__main__':
    unittest.main()
