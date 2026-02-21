import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List
from loguru import logger

from src.models.car import CarListing

class SupabaseManager:
    """
    管理與 Supabase 資料庫之間所有互動的類。
    負責初始化客戶端以及執行數據操作（如 upsert）。
    """
    def __init__(self):
        load_dotenv()
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("需要在 .env 文件中設置 Supabase 的 URL 和 KEY")
        
        self.client: Client = create_client(url, key)
        logger.info("Supabase 客戶端初始化成功。")

    def batch_upsert_cars(self, cars: List[CarListing], table_name: str = "market_listings"):
        """
        將一批 CarListing 物件批量上傳（upsert）到 Supabase 指定的表格中。

        "Upsert" 是一種智能操作：
        - 如果數據庫中已存在具有相同 `external_id` 的記錄，則更新該記錄。
        - 如果不存在，則插入一條新記錄。
        這可以有效避免數據重複，並時刻保持數據為最新狀態。

        @param cars: 一個包含 CarListing Pydantic 模型的列表。
        @param table_name: 目標表格的名稱，預設為 'market_listings'。
        """
        if not cars:
            logger.warning("車輛數據列表為空，跳過本次上傳操作。")
            return

        try:
            # 將 Pydantic 模型列表轉換為字典列表，這是 Supabase-py 庫要求的格式。
            # 使用 model_dump(mode='json') 可以確保數據格式正確。
            data_to_upsert = [car.model_dump(mode='json') for car in cars]

            logger.info(f"準備將 {len(data_to_upsert)} 筆數據上傳至 '{table_name}'...")
            
            # 執行 upsert 操作
            response = self.client.table(table_name).upsert(
                data_to_upsert,
                on_conflict="external_id"  # 指定 'external_id' 為衝突判斷的唯一鍵
            ).execute()
            
            # 檢查 API 返回的數據
            if response.data:
                 logger.success(f"成功將 {len(response.data)} 筆記錄上傳/更新至 '{table_name}'。")
            else:
                 # PostgREST 在數據未發生任何變更時可能不返回數據
                 logger.info("Upsert 操作已執行，但未返回新數據。這可能是因為所有記錄都已是最新狀態。")

        except Exception as e:
            logger.error(f"上傳數據至 Supabase 時發生嚴重錯誤: {e}")
            # 某些 Supabase 錯誤會包含更詳細的 'details'
            if hasattr(e, 'details'):
                logger.error(f"錯誤詳情: {e.details}")

