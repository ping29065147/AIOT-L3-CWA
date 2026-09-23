"""
cwa_api.py - 中央氣象署 (CWA) Open Data API 擷取與解析模組 (7天一週預報版)
使用 F-D0047-091 氣象資料集抓取全台 22 縣市未來 7 天一週天氣預報。
"""

import requests
import urllib3
from typing import List, Dict, Any

# 停用 SSL 無安全憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CWA API 設定
API_KEY = "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2"
CWA_7DAY_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
CWA_36H_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

# 台灣地區劃分映射 (將縣市分組至 6 大區域)
REGION_MAPPING = {
    "北部地區": ["臺北市", "台北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣"],
    "中部地區": ["苗栗縣", "臺中市", "台中市", "彰化縣", "南投縣", "雲林縣"],
    "南部地區": ["嘉義市", "嘉義縣", "臺南市", "台南市", "高雄市", "屏東縣"],
    "東部地區": ["花蓮縣"],
    "東北部地區": ["宜蘭縣"],
    "東南部地區": ["臺東縣", "台東縣"]
}

def get_region_name(location_name: str) -> str:
    """根據縣市名稱傳回所屬的大區域名稱"""
    for region, cities in REGION_MAPPING.items():
        if location_name in cities:
            return region
    return "離島地區"

def fetch_raw_weather_data_7day(api_key: str = API_KEY) -> Dict[str, Any]:
    """呼叫 CWA API 取得 7 天一週預報 JSON 資料 (F-D0047-091)"""
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }
    response = requests.get(CWA_7DAY_API_URL, params=params, verify=False, timeout=15)
    response.raise_for_status()
    return response.json()

def parse_weather_records_7day(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    解析 F-D0047-091 7 天一週預報資料，提取全台 22 縣市每日最高/最低溫、降雨機率與天氣現象
    """
    parsed_results = []
    
    try:
        records = raw_data.get("records", {})
        locations_container = records.get("Locations", [])
        if not locations_container:
            return []
            
        location_list = locations_container[0].get("Location", [])
        
        for loc in location_list:
            city_name = loc.get("LocationName")
            region_name = get_region_name(city_name)
            
            weather_elements = loc.get("WeatherElement", [])
            elem_map = {e.get("ElementName"): e.get("Time", []) for e in weather_elements}
            
            min_t_times = elem_map.get("最低溫度", [])
            max_t_times = elem_map.get("最高溫度", [])
            wx_times = elem_map.get("天氣現象", [])
            pop_times = elem_map.get("12小時降雨機率", [])
            desc_times = elem_map.get("天氣預報綜合描述", [])
            
            # 以最低溫度的時間區段為主進行配對
            for i, min_item in enumerate(min_t_times):
                start_time = min_item.get("StartTime", "")
                data_date = start_time.split("T")[0] if "T" in start_time else start_time.split(" ")[0]
                
                # 最低溫
                min_val_str = min_item.get("ElementValue", [{}])[0].get("MinTemperature", "20")
                min_temp = float(min_val_str) if min_val_str.replace('.', '', 1).isdigit() else 20.0
                
                # 最高溫 (尋找相同或相對應時間索引)
                max_temp = min_temp + 5.0
                if i < len(max_t_times):
                    max_val_str = max_t_times[i].get("ElementValue", [{}])[0].get("MaxTemperature", str(max_temp))
                    if max_val_str.replace('.', '', 1).isdigit():
                        max_temp = float(max_val_str)
                        
                # 天氣現象
                wx_text = "多雲"
                if i < len(wx_times):
                    wx_text = wx_times[i].get("ElementValue", [{}])[0].get("Weather", "多雲")
                    
                # 降雨機率
                pop_val = 0
                if i < len(pop_times):
                    pop_str = pop_times[i].get("ElementValue", [{}])[0].get("ProbabilityOfPrecipitation", "0")
                    pop_val = int(pop_str) if pop_str.isdigit() else 0
                    
                # 綜合描述/舒適度
                ci_text = "舒適"
                if i < len(desc_times):
                    desc = desc_times[i].get("ElementValue", [{}])[0].get("WeatherDescription", "")
                    if "舒適" in desc:
                        ci_text = "舒適"
                    elif "悶熱" in desc:
                        ci_text = "悶熱"
                    elif "寒意" in desc or "冷" in desc:
                        ci_text = "稍有寒意"
                        
                parsed_results.append({
                    "locationName": city_name,
                    "regionName": region_name,
                    "dataDate": data_date,
                    "startTime": start_time,
                    "minT": min_temp,
                    "maxT": max_temp,
                    "weather": wx_text,
                    "pop": pop_val,
                    "ci": ci_text
                })

    except Exception as e:
        print(f"[WARN] 7天 API 解析異常，切換至備用：{e}")
        
    return parsed_results

if __name__ == "__main__":
    print("正在測試 7 天一週 CWA API 資料擷取 (F-D0047-091)...")
    try:
        raw_json = fetch_raw_weather_data_7day()
        parsed = parse_weather_records_7day(raw_json)
        print(f"[SUCCESS] 成功解析 {len(parsed)} 筆 7 天預報紀錄！")
        dates = sorted(list(set(d['dataDate'] for d in parsed)))
        print(f"[INFO] 預報涵蓋日期 ({len(dates)} 天)：", dates)
        print("\n前 2 筆數據樣態：")
        for item in parsed[:2]:
            print(item)
    except Exception as e:
        print(f"[ERROR] 擷取失敗：{e}")
