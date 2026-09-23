"""
app.py - Taiwan Weather Forecast 互動式天氣預報 Web 應用程式 (Stage 5 旗艦版)
整合 CWA API + SQLite + Streamlit + Folium 地圖 + AI 出遊穿搭建議 + CSV 資料匯出。
"""

import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from database import sync_api_to_db, get_all_forecasts_df, init_db

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast Pro",
    page_icon="🌤️",
    layout="wide"
)

# 初始化資料庫
init_db()

# 6 大分區座標對照表
REGION_COORDS = {
    "北部地區": [25.0330, 121.5654],
    "中部地區": [24.1477, 120.6736],
    "南部地區": [22.6273, 120.3014],
    "東部地區": [23.9871, 121.6015],
    "東北部地區": [24.7570, 121.7530],
    "東南部地區": [22.7583, 121.1444],
    "離島地區": [23.5711, 119.5793]
}

# 22 縣市座標對照表
CITY_COORDS = {
    "臺北市": [25.0330, 121.5654], "台北市": [25.0330, 121.5654],
    "新北市": [24.9157, 121.6739], "基隆市": [25.1283, 121.7419],
    "桃園市": [24.9936, 121.3010], "新竹市": [24.8138, 120.9675],
    "新竹縣": [24.8383, 121.0177], "苗栗縣": [24.5602, 120.8214],
    "臺中市": [24.1477, 120.6736], "台中市": [24.1477, 120.6736],
    "彰化縣": [24.0518, 120.5161], "南投縣": [23.9610, 120.9719],
    "雲林縣": [23.7092, 120.4313], "嘉義市": [23.4801, 120.4491],
    "嘉義縣": [23.4588, 120.5740], "臺南市": [22.9997, 120.2270], "台南市": [22.9997, 120.2270],
    "高雄市": [22.6273, 120.3014], "屏東縣": [22.6713, 120.4879],
    "宜蘭縣": [24.7570, 121.7530], "花蓮縣": [23.9871, 121.6015],
    "臺東縣": [22.7583, 121.1444], "台東縣": [22.7583, 121.1444],
    "澎湖縣": [23.5711, 119.5793], "金門縣": [24.4493, 118.3766], "連江縣": [26.1505, 119.9499]
}

def get_temp_color(temp: float) -> str:
    """依據溫度傳回對應標籤顏色"""
    if temp < 20:
        return "blue"       # <20℃ 藍色
    elif temp <= 25:
        return "green"      # 20-25℃ 綠色
    elif temp <= 30:
        return "orange"     # 25-30℃ 橘色
    else:
        return "red"        # >30℃ 紅色

# 標題列
st.title("🌤️ Taiwan Weather Forecast 台灣氣象互動儀表板 Pro")
st.markdown("##### *從氣象資料到互動式天氣預報應用 | 用程式探索天氣 · 用資料看見台灣 · 用 AI 實現更多可能*")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 控制與篩選面板")
    if st.button("🔄 同步最新 CWA 氣象資料"):
        with st.spinner("正在向中央氣象署 API 抓取最新資料..."):
            count = sync_api_to_db()
            st.success(f"成功更新 {count} 筆預報紀錄！")
            st.rerun()

    st.markdown("---")
    df_all = get_all_forecasts_df()
    
    if df_all.empty:
        st.warning("資料庫尚無資料，請點擊上方按鈕進行同步。")
        st.stop()
        
    available_regions = list(df_all["regionName"].unique())
    selected_region = st.selectbox("🎯 選擇觀測地區 (Select Region)", available_regions)

    available_dates = sorted(df_all["dataDate"].unique())
    selected_date = st.selectbox("📅 選擇觀測日期 (Select Date)", available_dates)

    st.markdown("---")
    # CSV 導出下載按鈕
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載氣象資料 CSV",
        data=csv_data,
        file_name=f"Taiwan_Weather_Forecast_{selected_date}.csv",
        mime="text/csv"
    )

# 頂部 KPI 卡片區
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
df_today = df_all[df_all["dataDate"] == selected_date]

if not df_today.empty:
    max_t_all = df_today["maxT"].max()
    min_t_all = df_today["minT"].min()
    avg_pop_all = df_today["pop"].mean()
    total_count = len(df_today)
    
    col_m1.metric("🔥 全台最高溫", f"{max_t_all:.1f} °C")
    col_m2.metric("🧊 全台最低溫", f"{min_t_all:.1f} °C")
    col_m3.metric("🌧️ 平均降雨機率", f"{avg_pop_all:.0f} %")
    col_m4.metric("📊 觀測站數據筆數", f"{total_count} 筆")
st.markdown("---")

# 主頁籤
tab1, tab2, tab3 = st.tabs(["📊 區域氣溫趨勢與 AI 穿搭建議", "🗺️ 全台雙視角天氣地圖", "📋 完整觀測資料庫"])

# --- TAB 1: 區域趨勢與 AI 出遊建議 ---
with tab1:
    st.subheader(f"📍 {selected_region} - 一週溫差趨勢與出遊建議")
    
    df_region = df_all[df_all["regionName"] == selected_region].copy()
    
    # 警報與穿搭建議專區
    reg_max = df_region["maxT"].max()
    reg_min = df_region["minT"].min()
    reg_pop = df_region["pop"].max()
    reg_wx = df_region["weather"].iloc[0] if not df_region.empty else "多雲"
    reg_ci = df_region["ci"].iloc[0] if "ci" in df_region.columns else "舒適"
    
    c_alert1, c_alert2 = st.columns(2)
    with c_alert1:
        if reg_max >= 30:
            st.error(f"🚨 **高溫警報**：預估最高溫達 {reg_max:.0f}°C！外出請做好防曬，並隨時補充水分。")
        elif reg_min <= 20:
            st.info(f"🧥 **涼意提醒**：預估最低溫降至 {reg_min:.0f}°C，早晚溫差大，建議攜帶薄外套。")
        else:
            st.success(f"☀️ **天候良好**：平均氣溫約 {(reg_max+reg_min)/2:.1f}°C，體感為【{reg_ci}】。")
            
    with c_alert2:
        if reg_pop >= 30:
            st.warning(f"🌧️ **降雨預警**：最高降雨機率達 {reg_pop}%！出門請記得隨身攜帶雨具。")
        else:
            st.success(f"🌤️ **降雨率低**：降雨機率僅 {reg_pop}%，非常適合戶外活動！")

    st.markdown("#### 💡 AI 智慧出遊與穿搭建議")
    st.info(f"**建議穿搭**：當前天氣現象為「{reg_wx}」，舒適度【{reg_ci}】。建議著輕便通氣衣服，並視早晚溫差準備長袖洋蔥式穿法。")

    st.markdown("---")
    
    # 折線圖與資料表
    df_chart = df_region.groupby("dataDate").agg(
        MinT=("minT", "min"),
        MaxT=("maxT", "max"),
        PoP=("pop", "max")
    ).reset_index()
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown("##### 📈 最高溫 (MaxT) vs 最低溫 (MinT) 折線圖")
        st.line_chart(df_chart.set_index("dataDate")[["MaxT", "MinT"]], color=["#FF4B4B", "#1C83E1"])
        
    with col_c2:
        st.markdown("##### 📝 統計表格 (含降雨機率)")
        st.dataframe(df_chart.rename(columns={"dataDate":"日期", "MinT":"最低溫(°C)", "MaxT":"最高溫(°C)", "PoP":"降雨率(%)"}), use_container_width=True)

# --- TAB 2: 全台雙視角地圖 ---
with tab2:
    st.subheader(f"🗺️ 全台氣溫與降雨地圖 (日期：{selected_date})")
    
    map_mode = st.radio("🔍 選擇地圖檢視視角：", ["6 大分區視角", "全台 22 縣市視角"], horizontal=True)
    
    df_date = df_all[df_all["dataDate"] == selected_date]
    m = folium.Map(location=[23.8, 120.9], zoom_start=7.5, tiles="CartoDB positron")
    
    if map_mode == "6 大分區視角":
        region_stats = df_date.groupby("regionName").agg(
            avg_min=("minT", "min"),
            avg_max=("maxT", "max"),
            max_pop=("pop", "max")
        ).reset_index()
        
        for _, row in region_stats.iterrows():
            r_name = row["regionName"]
            min_t, max_t, pop = row["avg_min"], row["avg_max"], row["max_pop"]
            avg_t = (min_t + max_t) / 2.0
            coords = REGION_COORDS.get(r_name, [23.5, 120.5])
            color = get_temp_color(avg_t)
            
            popup_html = f"""
            <div style='font-family: sans-serif; width: 170px;'>
                <h4><b>{r_name}</b></h4>
                <hr style='margin: 4px 0;'>
                <b>📅 日期：</b>{selected_date}<br>
                <b>🌡️ 氣溫：</b>{min_t:.0f} ~ {max_t:.0f} ℃<br>
                <b>🌧️ 降雨機率：</b>{pop}%<br>
                <b>📊 平均溫：</b>{avg_t:.1f} ℃
            </div>
            """
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{r_name}: {min_t:.0f}~{max_t:.0f}℃ | 降雨 {pop}%",
                icon=folium.Icon(color=color, icon="cloud")
            ).add_to(m)
            
    else:  # 全台 22 縣市視角
        for _, row in df_date.iterrows():
            c_name = row["locationName"]
            min_t, max_t, pop = row["minT"], row["maxT"], row["pop"]
            wx = row["weather"]
            avg_t = (min_t + max_t) / 2.0
            coords = CITY_COORDS.get(c_name, [23.5, 120.5])
            color = get_temp_color(avg_t)
            
            popup_html = f"""
            <div style='font-family: sans-serif; width: 170px;'>
                <h4><b>{c_name}</b></h4>
                <hr style='margin: 4px 0;'>
                <b>🌤️ 天氣：</b>{wx}<br>
                <b>🌡️ 氣溫：</b>{min_t:.0f} ~ {max_t:.0f} ℃<br>
                <b>🌧️ 降雨率：</b>{pop}%
            </div>
            """
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{c_name}: {wx} {min_t:.0f}~{max_t:.0f}℃",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)

    st_folium(m, width=950, height=520)

# --- TAB 3: 完整資料庫 ---
with tab3:
    st.subheader("📋 資料庫實時預報庫 (TemperatureForecasts)")
    st.dataframe(df_all[['id', 'locationName', 'regionName', 'dataDate', 'startTime', 'minT', 'maxT', 'weather', 'pop', 'ci']], use_container_width=True)

# 頁尾資訊
st.markdown("---")
st.caption("AI 創新微課程 Taiwan Weather Forecast Pro | CWA API × JSON × Python × SQLite × Streamlit × Folium")
