from abc import ABC, abstractmethod
from typing import List
from src.models.car import CarListing
from loguru import logger

class BaseCrawler(ABC):
    def __init__(self, headless: bool = True):
        self.headless = headless
        # 設定 Log 格式，方便除錯
        self.logger = logger.bind(crawler=self.__class__.__name__)

    @abstractmethod
    async def fetch_listings(self, page: int = 1) -> List[CarListing]:
        """子類別必須實作此方法"""
        pass

    async def run(self, max_pages: int = 1):
        """通用執行邏輯"""
        self.logger.info(f"啟動爬蟲，預計抓取 {max_pages} 頁")
        all_cars = []
        for p in range(1, max_pages + 1):
            try:
                cars = await self.fetch_listings(page=p)
                all_cars.extend(cars)
                self.logger.success(f"第 {p} 頁完成，成功解析 {len(cars)} 筆")
            except Exception as e:
                self.logger.error(f"第 {p} 頁失敗: {e}")
        return all_cars