"""
ai_presenter.py - AI 氣象主播播報、旅遊適合度評估與極端天氣診斷模組
專為 Taiwan Weather Forecast 設計之智慧分析與文案生成邏輯。
"""

import pandas as pd
from typing import Dict, Any, List

def generate_weather_script(region_name: str, df_region: pd.DataFrame) -> str:
    """根據預報數據生成新聞播報口吻的 AI 氣象廣播文案"""
    if df_region.empty:
        return "暫無預報資料。"
        
    start_date = df_region["dataDate"].min()
    end_date = df_region["dataDate"].max()
    max_t = df_region["maxT"].max()
    min_t = df_region["minT"].min()
    max_pop = df_region["pop"].max()
    common_wx = df_region["weather"].mode()[0] if not df_region["weather"].empty else "多雲"
    
    script = f"""
【AI 氣象主播廣播稿 - {region_name}一週天氣特報】

各位觀眾與聽眾朋友大家好，我是您的 AI 氣象主播！
為您播報 {region_name} 從 {start_date} 至 {end_date} 的最新天氣動態：

🌤️ 整體天候概況：
本週 {region_name} 整體天氣型態以「{common_wx}」為主。
預估一週最高氣溫將來到 {max_t:.0f}°C，最低氣溫則降至 {min_t:.0f}°C，溫差約落在 {max_t - min_t:.0f}°C 之間。

🌧️ 降雨機率提醒：
本週區域內最高降雨機率預估為 {max_pop}%。
"""

    if max_pop >= 40:
        script += "⚠️ 特別提醒您，部分時段有局部陣雨機會，出門請務必隨身攜帶雨具，並注意路面濕滑安全！\n"
    else:
        script += "✨ 天氣相對穩定，降雨機率較低，相當適合規劃戶外出行或晾曬衣物。\n"

    if max_t >= 32:
        script += "🔥 氣溫偏高，午後體感較為悶熱，請大家戶外活動時防範中暑，多補充水分！\n"
    elif min_t <= 18:
        script += "🧥 早晚溫差顯著，涼意較明顯，建議早出晚歸的朋友洋蔥式穿搭並帶件薄外套保暖。\n"
    else:
        script += "😊 整體舒適度良好，祝大家本週擁有美好愉快的好心情！\n"

    return script.strip()

def assess_travel_suitability(region_name: str, df_region: pd.DataFrame) -> Dict[str, Any]:
    """計算戶外旅遊適合度指數 (0~100) 並給予活動與時間建議"""
    if df_region.empty:
        return {"score": 50, "status": "資料不足", "advice": "暫無數據", "best_time": "全天"}
        
    avg_max = df_region["maxT"].mean()
    avg_min = df_region["minT"].mean()
    max_pop = df_region["pop"].max()
    
    score = 100
    
    if max_pop > 50:
        score -= 35
    elif max_pop > 30:
        score -= 20
    elif max_pop > 10:
        score -= 5
        
    if avg_max > 33:
        score -= 20
    elif avg_max > 30:
        score -= 10
        
    if avg_min < 16:
        score -= 15
        
    score = max(10, min(100, score))
    
    if score >= 85:
        status = "🌟 非常適合旅遊"
        advice = "天候非常優良！十分適合露營、登山、自行車或各類戶外行程。"
        best_time = "上午 08:00 ~ 下午 17:00 (全天皆宜)"
    elif score >= 65:
        status = "🌤️ 適合旅遊"
        advice = "體感尚算舒適，建議安排野餐、觀光景點散步，午後請留意遮陽或備雨具。"
        best_time = "上午 08:30 ~ 中望 12:00 (避開午後高溫)"
    elif score >= 45:
        status = "⛅ 需備方案"
        advice = "降雨率稍高或偏熱，建議優先考慮美術館、觀光工廠、咖啡館等室內備案。"
        best_time = "上午涼爽時段或室內場館"
    else:
        status = "🌧️ 不宜戶外活動"
        advice = "天候較不穩定，請盡量避免前往山區或溪邊，適合室內休閒活動。"
        best_time = "室內行程為主"
        
    return {
        "score": score,
        "status": status,
        "advice": advice,
        "best_time": best_time
    }

def get_extreme_weather_alerts(df_all: pd.DataFrame) -> List[Dict[str, Any]]:
    """掃描全台 7 天氣象，列出高溫 (>32°C)、降雨 (>50%) 與極端低溫警告"""
    alerts = []
    if df_all.empty:
        return alerts
        
    for _, row in df_all.iterrows():
        c_name = row["locationName"]
        date_str = row["dataDate"]
        max_t = row["maxT"]
        min_t = row["minT"]
        pop = row["pop"]
        wx = row["weather"]
        
        if max_t >= 32:
            alerts.append({
                "type": "🔥 高溫警戒",
                "city": c_name,
                "date": date_str,
                "detail": f"最高溫達 {max_t:.0f}°C ({wx})"
            })
        if pop >= 50:
            alerts.append({
                "type": "🌧️ 暴雨預警",
                "city": c_name,
                "date": date_str,
                "detail": f"降雨機率達 {pop}% ({wx})"
            })
        if min_t <= 18:
            alerts.append({
                "type": "🧥 低溫涼意",
                "city": c_name,
                "date": date_str,
                "detail": f"最低溫降至 {min_t:.0f}°C ({wx})"
            })
            
    return alerts
