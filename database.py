"""
database.py - SQLite 資料庫建置、維護與查詢模組 (支援 7 天預報)
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any
from cwa_api import fetch_raw_weather_data_7day, parse_weather_records_7day

DB_PATH = "data.db"

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線"""
    return sqlite3.connect(db_path)

def init_db(db_path: str = DB_PATH) -> None:
    """初始化資料庫並自動補充缺少的欄位 (Schema Migration)"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        locationName TEXT NOT NULL,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        startTime TEXT NOT NULL,
        minT REAL NOT NULL,
        maxT REAL NOT NULL,
        weather TEXT,
        pop INTEGER DEFAULT 0,
        ci TEXT DEFAULT '舒適',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(locationName, startTime) ON CONFLICT REPLACE
    );
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        
        cursor.execute("PRAGMA table_info(TemperatureForecasts);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "pop" not in columns:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN pop INTEGER DEFAULT 0;")
        if "ci" not in columns:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN ci TEXT DEFAULT '舒適';")
            
        conn.commit()

def save_weather_data(records: List[Dict[str, Any]], db_path: str = DB_PATH) -> int:
    """將解析後的天候預報資料批量寫入/更新至資料庫"""
    if not records:
        return 0

    insert_sql = """
    INSERT INTO TemperatureForecasts (locationName, regionName, dataDate, startTime, minT, maxT, weather, pop, ci)
    VALUES (:locationName, :regionName, :dataDate, :startTime, :minT, :maxT, :weather, :pop, :ci);
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(insert_sql, records)
        conn.commit()
        return cursor.rowcount

def get_all_forecasts_df(db_path: str = DB_PATH) -> pd.DataFrame:
    """從資料庫讀取所有預報數據並轉為 Pandas DataFrame"""
    query = "SELECT * FROM TemperatureForecasts ORDER BY dataDate ASC, regionName ASC;"
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    return df

def get_region_forecasts_df(region_name: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """查詢特定大區域的天氣預報資料"""
    query = "SELECT * FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate ASC;"
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=(region_name,))
    return df

def sync_api_to_db(db_path: str = DB_PATH) -> int:
    """一鍵主動呼叫 7 天 API 並將最新資料寫入 SQLite 資料庫"""
    init_db(db_path)
    raw_data = fetch_raw_weather_data_7day()
    parsed_records = parse_weather_records_7day(raw_data)
    count = save_weather_data(parsed_records, db_path)
    return count

if __name__ == "__main__":
    print("正在執行 7 天資料庫初始化與 API 資料同步...")
    init_db()
    inserted_count = sync_api_to_db()
    print(f"[SUCCESS] 成功更新 {inserted_count} 筆 7 天氣象紀錄至 data.db！")
    
    df = get_all_forecasts_df()
    dates = sorted(df['dataDate'].unique())
    print(f"\n[INFO] 資料庫現有資料筆數：{len(df)}，涵蓋 {len(dates)} 天 ({dates[0]} ~ {dates[-1]})")
