from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class CarListing(BaseModel):
    """
    中古車盤源的 Pydantic 模型，此模型結構與 Supabase 中 'market_listings' 資料表
    (依據 2026-03-04 最新 SQL 腳本) 完全對應。
    """
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    # --- 核心識別與來源 (皆為必填) ---
    external_id: str = Field(..., description="在來源平台上的唯一標識符，用於 Upsert。")
    source_platform: str = Field("8891", description="數據來源平台。")
    link: str = Field(..., description="車輛的原始發布連結。")

    # --- 估價模型核心欄位 (皆為必填) ---
    brand: str = Field(..., description="品牌 (例如: 'BMW', 'Toyota')。")
    series: str = Field(..., description="車系 (例如: '3-Series', 'Corolla')。")
    year: int = Field(..., description="出廠年份 (例如: 2020)。")
    price_wan: float = Field(..., description="價格，單位為「萬」。")
    mileage_wan: float = Field(..., description="行駛里程，單位為「萬公里」。")
    
    # --- 詳細資訊 ---
    original_name: str = Field(..., description="在來源網站上顯示的原始標標題。")
    model_name: Optional[str] = Field(None, description="經過處理和標準化的車輛型號名稱。")
    color: Optional[str] = Field(None, description="車身顏色。")
    engine_displacement: Optional[int] = Field(None, description="引擎排氣量 (c.c.)。")
    fuel_type: Optional[str] = Field(None, description="燃料類型 (例如：汽油、柴油、油電)。")
    
    # --- 特徵標籤 (皆有預設值) ---
    is_verified: bool = Field(False, description="是否為認證車。")
    is_wagon: bool = Field(False, description="是否為旅行車。")
    has_4wd: bool = Field(False, description="是否具備四輪驅動功能。")
    
    # --- 媒體 (選填) ---
    image_url: Optional[str] = Field(None, description="代表性圖片的 URL。")
