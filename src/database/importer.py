# -*- coding: utf-8 -*-
"""
此腳本負責將中古車資料導入 PostgreSQL 資料庫。

可作為命令列工具使用，處理指定的 CSV 檔案。

主要功能：
1. 連接 PostgreSQL 資料庫。
2. 提供一個資料清理函式，特別是針對 'mileage' 欄位。
3. 實現 Upsert 邏輯：當車輛的 'external_id' 已存在時，更新特定欄位；
   否則，插入新紀錄。
4. 透過 fire 提供命令列介面，接收 CSV 檔案路徑。
"""

import os
import csv
import fire
import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine,
    Table,
    MetaData,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

# --- 資料庫設定 ---

def get_database_engine() -> Engine:
    """
    從環境變數讀取資料庫連線資訊，並建立 SQLAlchemy 引擎。
    """
    db_user = os.getenv("PG_USER", "postgres")
    db_password = os.getenv("PG_PASSWORD", "password")
    db_host = os.getenv("PG_HOST", "localhost")
    db_port = os.getenv("PG_PORT", "5432")
    db_name = os.getenv("PG_DB", "car_valuation")

    database_url = (
        f"postgresql+psycopg2://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    
    print(f"正在連接資料庫: postgresql+psycopg2://{db_user}:***@{db_host}:{db_port}/{db_name}")
    
    return create_engine(database_url)


# --- 資料表綱要定義 ---

metadata = MetaData()

market_listings = Table(
    'market_listings',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('external_id', String(100), nullable=False),
    Column('brand', String(50)),
    Column('series', String(100)),
    Column('year', Integer),
    Column('mileage', Float),
    Column('location', String(50)),
    Column('price', Float),
    Column('original_title', String(255)),
    Column('crawled_at', DateTime, default=datetime.datetime.utcnow),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow),
    UniqueConstraint('external_id', name='uq_external_id')
)


# --- 資料處理核心邏輯 ---

def clean_data(car_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    對車輛資料列表進行清理，特別是 mileage 欄位。
    """
    cleaned_list = []
    for car in car_data:
        mileage = car.get('mileage')
        
        if mileage is not None and (mileage == 0.0 or mileage > 1_000_000):
            print(f"偵測到異常里程數: {mileage} for external_id: {car.get('external_id')}, 將其標記為 None。")
            car['mileage'] = None
        
        cleaned_list.append(car)
        
    return cleaned_list

def upsert_cars(engine: Engine, car_data: List[Dict[str, Any]]):
    """
    將車輛資料執行 Upsert 操作到資料庫。
    """
    if not car_data:
        print("沒有資料需要處理。")
        return

    stmt = insert(market_listings).values(car_data)
    
    update_dict = {
        'price': stmt.excluded.price,
        'mileage': stmt.excluded.mileage,
        'crawled_at': datetime.datetime.utcnow(),
    }

    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=['external_id'],
        set_=update_dict
    )

    with engine.connect() as conn:
        result = conn.execute(upsert_stmt)
        conn.commit()
        print(f"操作完成。影響的資料筆數: {result.rowcount}")

# --- 命令列介面 ---

class ImporterCLI:
    """
    中古車資料導入工具的命令列介面。
    """

    def _load_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        從 CSV 檔案載入資料，並進行基本型別轉換。
        
        預期 CSV 標頭 (header) 包含:
        external_id, brand, series, year, mileage, location, price, original_title
        """
        print(f"正在從 {file_path} 讀取資料...")
        records = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    try:
                        # 進行型別轉換
                        row['year'] = int(row['year']) if row.get('year') else None
                        row['mileage'] = float(row['mileage']) if row.get('mileage') else None
                        row['price'] = float(row['price']) if row.get('price') else None
                        
                        # 加入爬取時間
                        row['crawled_at'] = datetime.datetime.utcnow()
                        
                        records.append(row)
                    except (ValueError, TypeError) as e:
                        print(f"警告：跳過格式錯誤的一行資料 {row}: {e}")
                        continue
        except FileNotFoundError:
            print(f"錯誤：找不到檔案 {file_path}")
            return []
            
        print(f"成功讀取 {len(records)} 筆資料。")
        return records

    def process_csv(self, file_path: str):
        """
        處理單一 CSV 檔案，將其內容導入資料庫。

        :param file_path: 要處理的 CSV 檔案的完整路徑。
        """
        print("--- 開始執行中古車資料導入腳本 ---")

        # 1. 建立資料庫引擎並準備資料表
        try:
            db_engine = get_database_engine()
            print("\n--- 步驟 1: 檢查並建立資料表 (如果需要) ---")
            metadata.create_all(db_engine)
            print("資料表檢查完成。")
        except Exception as e:
            print(f"資料庫連接或設定失敗: {e}")
            return

        # 2. 從 CSV 讀取資料
        print(f"\n--- 步驟 2: 從 CSV 檔案讀取資料 ---")
        car_data = self._load_from_csv(file_path)
        if not car_data:
            print("CSV 檔案為空或讀取失敗，腳本終止。")
            return

        # 3. 清理資料
        print("\n--- 步驟 3: 清理資料 ---")
        cleaned_cars = clean_data(car_data)
        print("資料清理完成。")

        # 4. 執行 Upsert
        print("\n--- 步驟 4: 執行 Upsert 操作 ---")
        try:
            upsert_cars(db_engine, cleaned_cars)
        except Exception as e:
            print(f"資料庫操作失敗: {e}")

        print("\n--- 腳本執行完畢 ---")

if __name__ == '__main__':
    fire.Fire(ImporterCLI)
