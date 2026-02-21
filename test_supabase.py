# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# -- Path Setup --
# 當從根目錄執行 'python3 test_supabase.py' 時，確保 src/ 套件可以被導入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.models.car import CarListing
    from src.database.supabase_client import SupabaseManager
except ModuleNotFoundError:
    logger.error("重要模組導入失敗。請確認您是從專案的根目錄 (CarValuation-V2) 執行此腳本。")
    logger.error(f"目前的 sys.path: {sys.path}")
    sys.exit(1)

# -- Configuration --
# 從 .env 檔案載入環境變數
load_dotenv()

# 設定 Loguru
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/test_supabase_{time}.log", level="DEBUG", rotation="10 MB")


def run_supabase_test():
    """
    執行一個完整的 Supabase 連線與資料上傳 (upsert) 測試。
    """
    logger.info("--- 開始 Supabase 連線測試 ---")

    # 1. 建立測試用的 CarListing 物件
    try:
        test_car = CarListing(
            source="supabase-test-regenerated",
            external_id=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            original_title="[Test] Regenerated Test Car",
            link="https://example.com/test-car-dont-delete-regenerated",
            brand="UNKNOWN",
            series="其他",
            processed_title="[Test] Regenerated Test Car",
            year=2025,
            price=88.8,
            mileage=5.0,
            location="虛擬城市",
            crawled_at=datetime.now()
        )
        logger.info("成功建立測試 CarListing 物件。")
    except Exception as e:
        logger.error(f"建立 CarListing 物件失敗: {e}")
        return

    # 2. 將物件轉換為字典，準備上傳
    # 使用 .model_dump() 而非 .dict() (Pydantic V2+)
    try:
        # Pydantic V2 uses model_dump()
        car_data_dict = test_car.model_dump()
        # Loguru 會自動處理 JSON 格式化，此處僅為示範
        pretty_json = json.dumps(
            car_data_dict,
            indent=2,
            ensure_ascii=False,
            default=str # for datetime object
        )
        logger.info(f"即將發送的測試資料:\n{pretty_json}")
    except Exception as e:
        logger.error(f"將 Pydantic 物件轉換為字典時發生錯誤: {e}")
        return

    # 3. 初始化 Supabase 管理器
    logger.info("正在初始化 SupabaseManager...")
    try:
        supabase_manager = SupabaseManager()
    except Exception as e:
        logger.error(f"初始化 SupabaseManager 失敗: {e}")
        return

    # 4. 執行批次上傳/更新
    logger.info("正在嘗試上傳測試資料至 'market_listings' 資料表...")
    try:
        # batch_upsert_cars 需要一個字典列表
        supabase_manager.batch_upsert_cars([car_data_dict])
    except Exception as e:
        # SupabaseManager 內部已有詳細的錯誤日誌，這裡只記錄測試失敗
        logger.error(f"測試過程中，執行 batch_upsert_cars 失敗。請檢查上方由 SupabaseManager 提供的錯誤日誌。")
        return

    logger.success("--- Supabase 連線測試成功結束 ---")
    logger.info("請檢查您在 Supabase 的 'market_listings' 資料表，確認資料已成功插入/更新。")


if __name__ == "__main__":
    run_supabase_test()
