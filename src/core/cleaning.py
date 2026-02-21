import re
import json
import os
import unicodedata
from typing import Dict, Any, Tuple
from loguru import logger

# --- 核心清洗與數值轉換函數 ---

def parse_unit_value(value_str: Any) -> float:
    """
    通用解析函數，用於處理帶有'萬'單位的價格或里程數。
    例如： "15.8萬" -> 15.8, "6萬公里" -> 6.0, 15.8 -> 15.8
    @param value_str: 包含數值的字符串或數字。
    @return: 轉換後的浮點數。若無法解析則返回 0.0。
    """
    if isinstance(value_str, (int, float)):
        return float(value_str)
    
    if not isinstance(value_str, str):
        return 0.0

    # 移除逗號和空白
    cleaned_str = value_str.replace(',', '').strip()
    
    # 使用正則表達式提取數字部分
    match = re.search(r'(\d+\.?\d*)', cleaned_str)
    if not match:
        return 0.0
        
    try:
        # 即使輸入是 "168000", 也只取 168000 這個數字
        return float(match.group(1))
    except (ValueError, TypeError):
        logger.warning(f"無法將 '{value_str}' 解析為數字，已返回 0.0")
        return 0.0

def refine_title(raw_title: str) -> str:
    """
    清洗原始標題，移除行銷術語、HTML標籤和其他噪音。
    @param raw_title: 爬蟲抓取的原始標題。
    @return: 清洗後的標題。
    """
    if not isinstance(raw_title, str):
        return ""

    # 移除 HTML 標籤
    text = re.sub(r'<[^>]+>', '', raw_title)
    # 移除特殊引號和內容
    text = re.sub(r'「[^」]*」', '', text)
    # 移除【】中的特定詞語
    text = re.sub(r'[【\[](?:總代理|自售|認證|實車實價)[】\]]', '', text)
    # 全形轉半形
    text = unicodedata.normalize('NFKC', text)
    # 移除多餘的空格
    text = ' '.join(text.split())
    
    return text.strip()

# --- 品牌與車系識別 ---

class CarIdentifier:
    """
    通過加載配置文件，從標題中識別車輛的品牌和車系。
    這是一個單例模式的實現，以避免重複加載配置。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CarIdentifier, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_dir: str = "config"):
        # 防止重複初始化
        if hasattr(self, 'initialized'):
            return
            
        self.brand_map = self._load_json(os.path.join(config_dir, "brand_map.json"), "BRAND_MAP")
        self.series_lookup = self._load_series_configs(os.path.join(config_dir, "series"))
        self.initialized = True
        logger.info("品牌/車系識別器已初始化完成")

    def _load_json(self, path: str, key: str) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get(key, {})
        except FileNotFoundError:
            logger.warning(f"配置文件未找到: {path}")
            return {}
        except Exception as e:
            logger.error(f"加載 {path} 失敗: {e}")
            return {}

    def _load_series_configs(self, series_dir: str) -> Dict:
        series_lookup = {}
        if not os.path.isdir(series_dir):
            logger.warning(f"車系配置目錄未找到: {series_dir}")
            return series_lookup
            
        for fname in os.listdir(series_dir):
            if fname.endswith(".json"):
                brand_key = fname.replace(".json", "").upper()
                series_lookup[brand_key] = self._load_json(os.path.join(series_dir, fname), None)
        return series_lookup

    def identify(self, title: str) -> Tuple[str, str]:
        """
        從給定的標題中識別品牌和車系。
        @param title: 清洗過的車輛標題。
        @return: 一個包含 (品牌, 車系) 的元組。
        """
        # 預設值
        brand, series = "UNKNOWN", "其他"

        # 1. 識別品牌
        for b_name, b_regex in self.brand_map.items():
            if re.search(b_regex, title, re.IGNORECASE):
                brand = b_name
                break
        
        # 2. 如果找到品牌，則繼續識別車系
        if brand != "UNKNOWN" and brand.upper() in self.series_lookup:
            best_match_len = 0
            for s_name, keywords in self.series_lookup[brand.upper()].items():
                for kw in keywords:
                    if kw.lower() in title.lower():
                        if len(kw) > best_match_len:
                            best_match_len = len(kw)
                            series = s_name
        
        return brand, series

# --- 主協調函數 ---

# 初始化一個全域的識別器實例
car_identifier = CarIdentifier(config_dir="config")

def clean_car_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    協調所有清洗步驟的主函數。
    接收爬蟲抓取的原始字典，返回一個結構化、清洗過的字典。
    
    @param raw_data: 包含 'original_title', 'price', 'mileage' 等鍵的原始字典。
    @return: 包含 'processed_title', 'brand', 'series', 'price', 'mileage' 等鍵的清洗後字典。
    """
    original_title = raw_data.get("original_title", "")
    
    # 1. 清洗標題
    processed_title = refine_title(original_title)
    
    # 2. 識別品牌和車系
    brand, series = car_identifier.identify(processed_title)
    
    # 3. 解析價格和里程
    price = parse_unit_value(raw_data.get("price"))
    mileage = parse_unit_value(raw_data.get("mileage"))
    
    # 4. 組裝並返回結果
    # 這裡只返回清洗後產生的新數據，原始數據（如 external_id, link, year）應由調用方合併
    return {
        "processed_title": processed_title,
        "brand": brand,
        "series": series,
        "price": price,
        "mileage": mileage,
    }