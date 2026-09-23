"""
config.py - 全局專案配置與環境變數管理模組
支援 CWA API Key、資料庫檔案路徑與預設設定。
"""

import os

# CWA API 預設授權碼 (可透過環境變數 CWA_API_KEY 覆蓋)
CWA_API_KEY = os.getenv("CWA_API_KEY", "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2")

# API URL 設定
CWA_7DAY_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
CWA_36H_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

# SQLite 資料庫設定
DB_PATH = os.getenv("DB_PATH", "data.db")

# 頁面標題設定
APP_TITLE = "Taiwan Weather Forecast 7 天氣象互動儀表板 Pro"
