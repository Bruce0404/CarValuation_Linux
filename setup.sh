#!/bin/bash
# 安裝 Python 依賴
pip install -r requirements.txt
# 安裝瀏覽器核心與系統依賴 (Linux 必備)
playwright install chromium
playwright install-deps