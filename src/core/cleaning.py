from __future__ import annotations
import re
import unicodedata
import json
import os
from loguru import logger
from typing import Tuple

# --- 移植自舊專案 lib/utils.py ---

def refine_original_name(raw_name: str) -> str:
    """
    清洗標題，移除行銷雜訊 (移植自 lib/utils.py)
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    # 1. 移除常見的 8891 網頁抓取雜訊
    refined = re.sub(r"距離您.*", "", raw_name)
    
    # 2. 移除重複的價格與年份標籤
    refined = re.sub(r"\d+\.?\d*萬.*", "", refined)
    refined = re.sub(r"20\d{2}年.*", "", refined)

    # 3. 移除行銷雜訊 (可擴充)
    marketing_keywords = [
        r"\d+歲即可貸", r"低利率", r"強力過件", r"信用小白", r"全額貸"
    ]
    refined = re.sub(r"(?i)(" + "|".join(marketing_keywords) + r").*", "", refined)

    # 4. 截斷邏輯
    return refined.split('「')[0].strip()

class CarIdentifier:
    """
    品牌與車系識別器 (邏輯移植自 lib/utils.py CarIdentifier)
    """
    def __init__(self, config_dir="config"):
        self.brand_map = {}
        self.series_lookup = {}
        # 預設載入
        self._load_config(config_dir)

    def _load_config(self, config_dir):
        # 載入 brand_map.json
        try:
            with open(os.path.join(config_dir, "brand_map.json"), "r", encoding="utf-8") as f:
                self.brand_map = json.load(f).get("BRAND_MAP", {})
        except Exception:
            logger.warning("⚠️ 找不到 brand_map.json，品牌識別將受限")

        # 載入 series/*.json
        series_dir = os.path.join(config_dir, "series")
        if os.path.exists(series_dir):
            for fname in os.listdir(series_dir):
                if fname.endswith(".json"):
                    brand_key = fname.replace(".json", "").upper()
                    try:
                        with open(os.path.join(series_dir, fname), "r", encoding="utf-8") as f:
                            self.series_lookup[brand_key] = json.load(f)
                    except Exception as e:
                        logger.error(f"無法讀取車系檔 {fname}: {e}")

    def _clean_title(self, title: str) -> str:
        text = unicodedata.normalize('NFKC', title)
        text = re.sub(r"[【\[《『](?:置頂|總代理|自售|實車實價|HOT|SAVE|SUM)[】\]》』]?", "", text)
        return re.sub(r"\s+", " ", text).lower().strip()

    def identify(self, title: str, original_brand: str = "UNKNOWN") -> Tuple[str, str]:
        """
        輸入標題，回傳 (品牌, 車系)
        """
        clean_title = self._clean_title(title)
        
        # 1. 簡單品牌辨識 (可擴充舊專案的複雜邏輯)
        brand = original_brand
        for b_name, b_regex in self.brand_map.items():
            if re.search(b_regex, clean_title, re.IGNORECASE):
                brand = b_name
                break
        
        # 2. 車系辨識
        series = "其他"
        brand_key = str(brand).upper()
        
        if brand_key in self.series_lookup:
            # 尋找最長匹配的關鍵字
            best_match_len = 0
            for s_name, keywords in self.series_lookup[brand_key].items():
                for kw in keywords:
                    if kw.lower() in clean_title:
                        if len(kw) > best_match_len:
                            best_match_len = len(kw)
                            series = s_name
        
        return brand, series