from pydantic import BaseModel, Field
from typing import Optional

class CarListing(BaseModel):
    """
    中古車盤源的 Pydantic 模型，用於數據驗證與結構化。
    此模型與 Supabase 中的 'market_listings' 資料表結構完全對應。
    """
    # --- 核心識別欄位 ---
    external_id: str = Field(..., description="在來源平台上的唯一標識符，用於 Upsert 操作。")
    link: str = Field(..., description="車輛的原始發布連結，應具有唯一性。")

    # --- 基本車輛資訊 ---
    original_name: str = Field(..., description="在來源網站上顯示的原始標題。")
    model_name: Optional[str] = Field(None, description="經過處理和標準化的車輛型號名稱。")
    
    # --- 價格與里程 ---
    price_wan: float = Field(..., description="價格，單位為「萬」。")
    mileage_wan: Optional[float] = Field(None, description="行駛里程，單位為「萬公里」。")

    # --- 車輛規格與特徵 ---
    color: Optional[str] = Field(None, description="車身顏色。")
    engine_displacement: Optional[int] = Field(None, description="引擎排氣量 (c.c.)。")
    fuel_type: Optional[str] = Field(None, description="燃料類型 (例如：汽油、柴油、油電)。")
    
    # --- 狀態與來源 ---
    source_platform: str = Field("8891", description="數據來源平台，預設為 '8891'。")
    is_verified: bool = Field(False, description="是否為認證車。")
    
    # --- 特殊屬性 ---
    is_wagon: bool = Field(False, description="是否為旅行車。")
    has_4wd: bool = Field(False, description="是否具備四輪驅動功能。")
    
    # --- 媒體 ---
    image_url: Optional[str] = Field(None, description="代表性圖片的 URL。")
    
    class Config:
        from_attributes = True  # 相容 Pydantic V2，允許從 ORM 模型或其他屬性對象創建
        anystr_strip_whitespace = True  # 自動去除字串前後的空白
        use_enum_values = True  # 如果有使用 Enum，確保其值被正確使用
