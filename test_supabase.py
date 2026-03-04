import os
import sys
from dotenv import load_dotenv
from loguru import logger

# --- 專案根目錄設定 ---
# 確保腳本在專案根目錄下執行時，能夠正確導入 src 中的模組
try:
    # 這會將當前腳本的目錄添加到 sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from src.database.supabase_client import SupabaseManager
    from src.models.car import CarListing

except ImportError as e:
    logger.error(f"重要模組導入失敗。請確認您是從專案的根目錄執行此腳本。")
    logger.error(f"目前的 sys.path: {sys.path}")
    sys.exit(1)

def run_test():
    """
    執行 Supabase 連線與資料上傳測試。
    """
    load_dotenv()
    logger.info("開始執行 Supabase 連線測試...")

    try:
        # 1. 初始化 Supabase 管理器
        supabase_manager = SupabaseManager()
        logger.info("SupabaseManager 初始化成功。")

        # 2. 準備測試數據 (與最新的 CarListing 必填欄位完全對齊)
        test_data = [
            CarListing(
                external_id="test-car-001",
                link="https://example.com/car/001",
                brand="TestBrand",
                series="TestSeries-Sedan", # 必填
                year=2023,                  # 必填
                mileage_wan=5.5,            # 必填
                original_name="【測試車輛】豪華版轎車",
                model_name="Test Sedan Deluxe",
                price_wan=88.8,
                color="白色",
                engine_displacement=1998,
                fuel_type="汽油",
                source_platform="test_script",
                is_verified=True,
                is_wagon=False,
                has_4wd=False,
                image_url="https://example.com/img/001.jpg"
            ),
            CarListing(
                external_id="test-car-002",
                link="https://example.com/car/002",
                brand="TestBrand",
                series="TestSeries-SUV",     # 必填
                year=2021,                  # 必填
                mileage_wan=2.1,            # 必填
                original_name="【測試更新】運動休旅",
                model_name="Test SUV Sport",
                price_wan=120.5,
                color="黑色",
                engine_displacement=2999,
                fuel_type="柴油",
                source_platform="test_script",
                is_verified=False,
                is_wagon=False,
                has_4wd=True,
                image_url="https://example.com/img/002.jpg"
            ),
             CarListing(
                external_id="test-car-003",
                link="https://example.com/car/003",
                brand="TestBrand",
                series="TestSeries-Wagon",  # 必填
                year=2024,                  # 必填
                mileage_wan=1.1,            # 必填
                original_name="【稀有旅行車】",
                model_name="Test Wagon Rare",
                price_wan=150.0,
                color="藍色",
                engine_displacement=2498,
                fuel_type="油電",
                source_platform="test_script",
                is_verified=True,
                is_wagon=True,
                has_4wd=True,
                image_url="https://example.com/img/003.jpg"
            )
        ]
        logger.info(f"已準備 {len(test_data)} 筆測試數據。")

        # 3. 執行批量上傳/更新操作
        supabase_manager.batch_upsert_cars(test_data, table_name="market_listings")
        
        logger.success("Supabase batch_upsert_cars 測試執行完畢。請至 Supabase 後台檢查 'market_listings' 表格中的數據。")

    except ValueError as ve:
        logger.error(f"環境變數設定錯誤: {ve}")
    except Exception as e:
        logger.error(f"測試過程中發生未預期的錯誤: {e}")

if __name__ == "__main__":
    # 配置 Loguru
    logger.add(
        "logs/test_supabase.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    run_test()
