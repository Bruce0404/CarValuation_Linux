
import asyncio
from loguru import logger
import sys
import os

# 確保能夠從 src 目錄導入模組
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.platforms.site_8891 import Crawler8891, ListContainerNotFound
except ImportError as e:
    logger.error(f"無法導入 Crawler8891: {e}。請確保您在專案根目錄下執行此腳本。")
    sys.exit(1)

async def main():
    """
    執行 8891 爬蟲的調試腳本（基於 Playwright）。
    """
    logger.add("logs/debug_8891.log", rotation="10 MB", level="DEBUG")
    logger.info("--- 開始執行 8891 爬蟲調試腳本 ---")

    # 初始化爬蟲，可以設置 headless=False 來觀察過程
    crawler = Crawler8891(headless=True)

    try:
        await crawler.launch_browser()
        
        # 抓取第一頁的數據
        listings = await crawler.fetch_listings(page_num=1)

        if listings:
            logger.success(f"成功抓取到 {len(listings)} 筆車輛數據。")
            logger.info("--- 前 3 筆數據預覽 ---")
            for i, car in enumerate(listings[:3]):
                logger.info(f"  車輛 {i+1}:")
                logger.info(f"    - 品牌: {car.brand}")
                logger.info(f"    - 車系: {car.series}")
                logger.info(f"    - 年份: {car.year}")
                logger.info(f"    - 價格: {car.price_wan} 萬")
                logger.info(f"    - 里程: {car.mileage_wan} 萬公里")
                logger.info(f"    - 連結: {car.link}")
        else:
            logger.warning("未能抓取到任何車輛數據。請檢查網站結構或爬蟲邏輯。")

    except ListContainerNotFound:
        logger.error("由於找不到列表容器，腳本提前終止。")
    except Exception as e:
        logger.opt(exception=True).error(f"執行爬蟲時發生未預期的錯誤: {e}")

    finally:
        await crawler.close_browser()
        logger.info("--- 8891 爬蟲調試腳本執行完畢 ---")

if __name__ == "__main__":
    # 使用 asyncio.run 來執行異步的 main 函數
    asyncio.run(main())
