import fire
import asyncio
import sys
import os
from loguru import logger

# 確保可以找到 src 模組
sys.path.append(os.getcwd())

from src.platforms.site_8891 import Crawler8891
from src.models.car import CarListing
from src.database.supabase_client import SupabaseManager

class CarBotCLI:
    def crawl(self, source: str = '8891', pages: int = 1, headless: bool = True):
        """
        執行爬蟲任務
        :param source: 來源平台 (預設 8891)
        :param pages: 抓取頁數
        :param headless: 是否隱藏瀏覽器 (WSL 環境建議設為 True，除非您有設定 X-Server)
        """
        if source == '8891':
            # 1. 爬蟲執行
            crawler = Crawler8891(headless=headless)
            results: list[CarListing] = asyncio.run(crawler.run(max_pages=pages))
            
            logger.info(f"--- 共擷取 {len(results)} 筆資料 ---")
            
            if not results:
                logger.warning("沒有擷取到任何資料，流程結束。")
                return

            # 2. 數據同步至 Supabase
            logger.info("準備將資料同步至 Supabase...")
            try:
                supabase_manager = SupabaseManager()
                supabase_manager.batch_upsert_cars(results)
            except Exception as e:
                logger.error(f"同步至 Supabase 時發生錯誤: {e}")
                
        else:
            logger.warning(f"尚未支援: {source}")

if __name__ == '__main__':
    fire.Fire(CarBotCLI)