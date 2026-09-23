"""
cwa_api.py - 中央氣象署 (CWA) Open Data API 擷取與解析模組 (進階版)
用於從 CWA API 抓取縣市預報資料（包含 MinT, MaxT, Wx, PoP 降雨機率, CI 舒適度）。
"""

import requests
import urllib3
from typing import List, Dict, Any

# 停用 SSL 無安全憑證警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CWA API 設定
API_KEY = "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2"
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

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

def fetch_raw_weather_data(api_key: str = API_KEY) -> Dict[str, Any]:
    """呼叫 CWA API 取得原始 JSON 資料"""
    params = {
        "Authorization": api_key,
        "format": "JSON"
    }
    response = requests.get(CWA_API_URL, params=params, verify=False, timeout=10)
    response.raise_for_status()
    return response.json()

def parse_weather_records(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    解析 JSON 資料，提取氣溫 (MinT/MaxT)、天氣現象 (Wx)、降雨機率 (PoP) 與舒適度 (CI)
    """
    records = raw_data.get("records", {})
    location_list = records.get("location", [])
    
    parsed_results = []
    
    for loc in location_list:
        city_name = loc.get("locationName")
        region_name = get_region_name(city_name)
        
        weather_elements = loc.get("weatherElement", [])
        min_t_elem = next((item for item in weather_elements if item.get("elementName") == "MinT"), None)
        max_t_elem = next((item for item in weather_elements if item.get("elementName") == "MaxT"), None)
        wx_elem = next((item for item in weather_elements if item.get("elementName") == "Wx"), None)
        pop_elem = next((item for item in weather_elements if item.get("elementName") == "PoP"), None)
        ci_elem = next((item for item in weather_elements if item.get("elementName") == "CI"), None)
        
        if not min_t_elem or not max_t_elem:
            continue
            
        times_count = len(min_t_elem.get("time", []))
        for i in range(times_count):
            time_info = min_t_elem["time"][i]
            start_time = time_info.get("startTime", "")
            data_date = start_time.split(" ")[0] if " " in start_time else start_time.split("T")[0]
            
            min_temp = float(min_t_elem["time"][i]["parameter"]["parameterName"])
            max_temp = float(max_t_elem["time"][i]["parameter"]["parameterName"])
            wx_text = wx_elem["time"][i]["parameter"]["parameterName"] if wx_elem else "多雲"
            
            pop_val = 0
            if pop_elem and i < len(pop_elem.get("time", [])):
                pop_str = pop_elem["time"][i]["parameter"].get("parameterName", "0")
                pop_val = int(pop_str) if pop_str.isdigit() else 0
                
            ci_text = "舒適"
            if ci_elem and i < len(ci_elem.get("time", [])):
                ci_text = ci_elem["time"][i]["parameter"].get("parameterName", "舒適")
            
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
            
    return parsed_results

if __name__ == "__main__":
    print("正在測試進階 CWA API 資料擷取 (含 PoP & CI)...")
    try:
        raw_json = fetch_raw_weather_data()
        parsed = parse_weather_records(raw_json)
        print(f"[SUCCESS] 成功解析 {len(parsed)} 筆完整氣象紀錄。")
        print("前 2 筆數據對照：")
        for item in parsed[:2]:
            print(item)
    except Exception as e:
        print(f"[ERROR] 擷取失敗：{e}")
