from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from datetime import datetime
from typing import Optional
# 引入剛剛建立的清洗模組
from src.core.cleaning import CarIdentifier, refine_original_name

# 初始化識別器 (全域單例，避免重複讀取檔案)
identifier = CarIdentifier()

class CarListing(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    source: str
    external_id: str
    
    # 原始資料
    original_title: str = Field(..., alias="title") # 接收爬蟲抓到的原始標題
    link: str
    
    # 清洗後資料 (這些欄位由 validator 自動產生，爬蟲不用填)
    brand: str = "UNKNOWN"
    series: str = "其他"
    processed_title: str = ""
    
    year: int = Field(..., ge=1990, le=2026)
    price: float = Field(..., ge=0)
    mileage: float = Field(default=0.0)
    location: str
    crawled_at: datetime = Field(default_factory=datetime.now)

    @field_validator('price', mode='before')
    def parse_price(cls, v):
        if isinstance(v, (int, float)): return float(v)
        if isinstance(v, str):
            clean = v.replace('萬', '').replace(',', '').strip()
            return float(clean) if clean.replace('.', '').isdigit() else 0.0
        return 0.0

    @model_validator(mode='after')
    def compute_metadata(self):
        """
        自動計算清洗後的標題、品牌與車系
        """
        # 1. 標題去雜訊
        self.processed_title = refine_original_name(self.original_title)
        
        # 2. 辨識品牌車系 (預設使用 UNKNOWN 作為原始品牌提示)
        # 如果爬蟲有傳入 brand 可以在這裡優化，目前先用標題硬解
        detected_brand, detected_series = identifier.identify(self.processed_title)
        
        self.brand = detected_brand
        self.series = detected_series
        
        return self