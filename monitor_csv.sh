#!/bin/bash

# ==============================================================================
# CSV 檔案自動處理腳本
#
# 功能:
#   - 監控指定的 "inbox" 資料夾。
#   - 當有新的 CSV 檔案被建立或移入時，觸發 Python 資料導入腳本。
#   - 處理完成後，將 CSV 檔案移動到 "processed" 資料夾以作備份，
#     避免重複處理。
#
# 依賴:
#   - inotify-tools: 一個 Linux 核心的檔案系統事件監控工具。
#     在 Debian/Ubuntu 上安裝: sudo apt-get update && sudo apt-get install inotify-tools
#
# 如何與 OpenClaw 協作:
#   這個腳本是一個獨立的守護進程 (daemon)。在您的 OpenClaw 專案或任何
#   其他系統中，您只需要確保爬蟲或其他資料來源產生的 CSV 檔案最終被
#   儲存到這個腳本所監控的 WATCH_DIR 資料夾即可。腳本會自動完成後續的
#   資料庫導入工作，實現系統間的解耦。
# ==============================================================================

# --- 設定 ---

# 取得腳本所在的目錄，以確保無論在哪裡執行，路徑都是正確的
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 要監控的資料夾
WATCH_DIR="$BASE_DIR/csv_inbox"

# 處理完成後，檔案要移至的資料夾
PROCESSED_DIR="$BASE_DIR/csv_processed"

# 要執行的 Python 導入腳本
PYTHON_SCRIPT="$BASE_DIR/src/database/importer.py"

# --- 檢查依賴 ---

if ! command -v inotifywait &> /dev/null
then
    echo "錯誤: 'inotifywait' 指令不存在。"
    echo "請先安裝 'inotify-tools' 套件。"
    echo "在 Debian/Ubuntu 上，請執行: sudo apt-get update && sudo apt-get install inotify-tools"
    exit 1
fi

echo "✅ 依賴檢查完成 ('inotifywait' 已安裝)。"

# --- 主迴圈 ---

echo "🚀 開始監控資料夾: $WATCH_DIR"
echo "   按下 Ctrl+C 以停止腳本。"

# -m: 持續監控
# -e create: 只監控檔案建立事件
# -e moved_to: 監控檔案被移入的事件
# --format '%w%f': 輸出 "目錄路徑/檔案名稱"
inotifywait -m -e create -e moved_to --format '%w%f' "$WATCH_DIR" | while read NEW_FILE_PATH
do
    echo "---"
    echo "$(date): 偵測到新檔案: $NEW_FILE_PATH"

    # 檢查是否為 CSV 檔案
    if [[ "$NEW_FILE_PATH" == *.csv ]]; then
        echo "   [1/3] 確認為 CSV 檔案。開始處理..."

        # 呼叫 Python 腳本進行處理
        # 注意：這裡假設您已經設定好 Python 環境和資料庫環境變數
        echo "   [2/3] 執行 Python 導入腳本..."
        python3 "$PYTHON_SCRIPT" process_csv --file-path="$NEW_FILE_PATH"
        
        # 檢查 Python 腳本的返回碼
        if [ $? -eq 0 ]; then
            echo "   ✅ Python 腳本執行成功。"
            # 將處理完的檔案移動到備份區
            echo "   [3/3] 將檔案移動至: $PROCESSED_DIR"
            mv "$NEW_FILE_PATH" "$PROCESSED_DIR/"
            echo "   ✅ 處理完成。"
        else
            echo "   ❌ 錯誤: Python 腳本執行失敗。"
            echo "   檔案 '$NEW_FILE_PATH' 將保留在原地以便檢查。"
        fi
    else
        echo "   ⚠️  跳過非 CSV 檔案: $NEW_FILE_PATH"
    fi
done
