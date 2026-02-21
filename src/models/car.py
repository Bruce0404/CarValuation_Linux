from pydantic import BaseModel, Field
from typing import Optional

class CarListing(BaseModel):
    """
    定義一筆汽車市場資訊的數據模型 (Data Model)。
    這個模型對應於 Supabase 資料庫中的 `market_listings` 表格。
    Pydantic 會自動驗證傳入數據的類型，確保數據一致性。
    """
    
    # === 必填欄位 (Required Fields) ===
    # 這些是構成一筆有效車輛資訊的核心數據。
    
    source: str = Field(..., description="數據來源平台，例如 'site_8891'")
    external_id: str = Field(..., description="來源平台上的唯一標識符，用於 upsert 操作")
    link: str = Field(..., description="車輛資訊頁面的原始連結")
    year: int = Field(..., ge=1990, le=2026, description="車輛製造年份，範圍限制在 1990-2026")
    price: float = Field(..., description="車輛售價，單位為（萬）")
    mileage: float = Field(..., description="車輛行駛里程，單位為（萬公里）")

    # === 選填欄位 (Optional Fields) ===
    # 這些欄位提供了更豐富的資訊，但不一定每筆數據都存在。
    
    original_title: Optional[str] = Field(None, description="爬蟲抓取到的原始、未經處理的標題")
    processed_title: Optional[str] = Field(None, description="經過清洗和標準化後的標題")
    brand: Optional[str] = Field(None, description="從標題中識別出的車輛品牌")
    series: Optional[str] = Field(None, description="從標題中識別出的車系")
    location: Optional[str] = Field(None, description="車輛所在的地理位置")

    # Pydantic v2 的 model_config，可以進行一些模型的額外配置
    class Config:
        # Pydantic 將能更好地處理 ORM 對象，雖然我們目前沒直接用 ORM
        orm_mode = True
        # 允許模型接收額外未定義的欄位而不拋出錯誤
        extra = 'ignore'