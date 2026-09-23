"""
test_suite.py - 自動化測試腳本 (Automated Test Suite)
涵蓋 CWA API 抓取、SQLite 資料庫寫入去重、AI 播報生成與地圖座標映射驗證。
"""

import unittest
import os
import gc
import pandas as pd
from cwa_api import fetch_raw_weather_data_7day, parse_weather_records_7day
from database import init_db, save_weather_data
from ai_presenter import generate_weather_script, assess_travel_suitability
from app import CITY_COORDS

class TestTaiwanWeatherApp(unittest.TestCase):
    
    def test_01_cwa_api_fetch(self):
        """測試 CWA API 7 天預報資料擷取與解析"""
        raw_data = fetch_raw_weather_data_7day()
        self.assertIsNotNone(raw_data, "API 回傳不應為空")
        parsed = parse_weather_records_7day(raw_data)
        self.assertGreater(len(parsed), 0, "解析筆數應大於 0")
        
        first_item = parsed[0]
        self.assertIn("locationName", first_item)
        self.assertIn("minT", first_item)
        self.assertIn("maxT", first_item)
        self.assertIn("pop", first_item)
        print(f"\n[OK] API 測試通過！解析 {len(parsed)} 筆資料，第一筆為：{first_item['locationName']}")

    def test_02_database_operations(self):
        """測試 SQLite 資料庫初始化與去重寫入"""
        test_db = "test_data.db"
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except Exception:
                pass
                
        init_db(test_db)
        sample_records = [
            {
                "locationName": "臺北市",
                "regionName": "北部地區",
                "dataDate": "2026-09-23",
                "startTime": "2026-09-23T12:00:00+08:00",
                "minT": 25.0,
                "maxT": 30.0,
                "weather": "多雲",
                "pop": 10,
                "ci": "舒適"
            }
        ]
        count1 = save_weather_data(sample_records, test_db)
        self.assertEqual(count1, 1, "應寫入 1 筆")
        
        count2 = save_weather_data(sample_records, test_db)
        self.assertEqual(count2, 1, "重複寫入應替換而不增加筆數")
        
        gc.collect()
        try:
            os.remove(test_db)
        except Exception:
            pass
            
        print("[OK] 資料庫寫入與去重測試通過！")

    def test_03_ai_presenter(self):
        """測試 AI 氣象播報與旅遊指數生成"""
        df_test = pd.DataFrame([{
            "dataDate": "2026-09-23",
            "maxT": 31.0,
            "minT": 24.0,
            "pop": 20,
            "weather": "多雲",
            "ci": "舒適"
        }])
        script = generate_weather_script("北部地區", df_test)
        self.assertIn("北部地區", script)
        self.assertIn("AI 氣象主播廣播稿", script)
        
        travel_eval = assess_travel_suitability("北部地區", df_test)
        self.assertGreaterEqual(travel_eval["score"], 0)
        self.assertLessEqual(travel_eval["score"], 100)
        print("[OK] AI 播報稿與旅遊指數生成測試通過！")

    def test_04_coordinates_completeness(self):
        """測試全台 22 縣市地圖座標完整性"""
        cities = ["臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市", "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"]
        for c in cities:
            self.assertIn(c, CITY_COORDS, f"縣市 {c} 應包含座標配置")
        print("[OK] 全台 22 縣市地圖座標驗證通過！")

if __name__ == "__main__":
    print("=== 開始執行 Taiwan Weather Forecast 全套自動化單元測試 ===\n")
    unittest.main()
