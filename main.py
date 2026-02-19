import fire
import asyncio
import sys
import os

# 確保可以找到 src 模組
sys.path.append(os.getcwd())

from src.platforms.site_8891 import Crawler8891

class CarBotCLI:
    def crawl(self, source: str = '8891', pages: int = 1, headless: bool = True):
        """
        執行爬蟲任務
        :param source: 來源平台 (預設 8891)
        :param pages: 抓取頁數
        :param headless: 是否隱藏瀏覽器 (WSL 環境建議設為 True，除非您有設定 X-Server)
        """
        if source == '8891':
            crawler = Crawler8891(headless=headless)
            results = asyncio.run(crawler.run(max_pages=pages))
            
            print(f"\n--- 成功擷取 {len(results)} 筆資料 ---")
            # 印出前 3 筆做檢查
            for car in results[:3]:
                print(car.model_dump_json(exclude={'link'}, indent=2))
        else:
            print(f"尚未支援: {source}")

if __name__ == '__main__':
    fire.Fire(CarBotCLI)