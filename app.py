"""
app.py - Taiwan Weather Forecast 互動式天氣預報 Web 應用程式
使用 Streamlit + SQLite + Folium 打造之台灣氣象觀測儀表板。
"""

import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from database import sync_api_to_db, get_all_forecasts_df, init_db

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast",
    page_icon="🌤️",
    layout="wide"
)

# 初始化資料庫
init_db()

# 區域座標對照表 (中心點緯度, 經度)
REGION_COORDS = {
    "北部地區": [25.0330, 121.5654],
    "中部地區": [24.1477, 120.6736],
    "南部地區": [22.6273, 120.3014],
    "東部地區": [23.9871, 121.6015],
    "東北部地區": [24.7570, 121.7530],
    "東南部地區": [22.7583, 121.1444]
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
st.title("🌤️ Taiwan Weather Forecast 台灣天氣預報儀表板")
st.markdown("##### *從氣象資料到互動式天氣預報應用 | 用程式探索天氣 · 用資料看見台灣*")

# 側邊欄：同步資料與篩選
with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🔄 同步最新 CWA 氣象資料"):
        with st.spinner("正在向中央氣象署抓取最新資料..."):
            count = sync_api_to_db()
            st.success(f"成功更新 {count} 筆預報資料！")
            st.rerun()

    st.markdown("---")
    # 讀取資料庫
    df_all = get_all_forecasts_df()
    
    if df_all.empty:
        st.warning("資料庫尚無資料，請點擊上方按鈕進行同步。")
        st.stop()
        
    available_regions = list(REGION_MAPPING_KEYS := df_all["regionName"].unique())
    selected_region = st.selectbox("🎯 選擇觀測地區 (Select Region)", available_regions)

    available_dates = sorted(df_all["dataDate"].unique())
    selected_date = st.selectbox("📅 選擇觀測日期 (Select Date)", available_dates)

# 主要分頁卡
tab1, tab2, tab3 = st.tabs(["📊 區域氣溫趨勢與數據", "🗺️ 台灣互動天氣地圖", "📋 完整資料庫觀測表"])

# --- TAB 1: 區域趨勢與數據 ---
with tab1:
    st.subheader(f"📍 {selected_region} - 一週最高與最低氣溫趨勢")
    
    df_region = df_all[df_all["regionName"] == selected_region].copy()
    
    # 依日期群組計算最高溫與最低溫平均
    df_chart = df_region.groupby("dataDate").agg(
        MinT=("minT", "min"),
        MaxT=("maxT", "max")
    ).reset_index()
    
    # 繪製折線圖
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("##### 📈 溫差變化折線圖 (MaxT vs MinT)")
        st.line_chart(df_chart.set_index("dataDate")[["MaxT", "MinT"]], color=["#FF4B4B", "#1C83E1"])
        
    with col2:
        st.markdown("##### 📝 數據清單表格")
        st.dataframe(df_chart, use_container_width=True)

# --- TAB 2: 台灣互動地圖 ---
with tab2:
    st.subheader(f"🗺️ 全台區域氣溫地圖 (觀測日期：{selected_date})")
    
    df_date = df_all[df_all["dataDate"] == selected_date]
    
    # 建立 Folium 地圖，以台灣中心點定位
    m = folium.Map(location=[23.8, 120.9], zoom_start=7.5, tiles="CartoDB positron")
    
    # 計算該日期各地區平均最高與最低溫
    region_stats = df_date.groupby("regionName").agg(
        avg_min=("minT", "min"),
        avg_max=("maxT", "max")
    ).reset_index()
    
    for _, row in region_stats.iterrows():
        r_name = row["regionName"]
        min_t = row["avg_min"]
        max_t = row["avg_max"]
        avg_t = (min_t + max_t) / 2.0
        
        coords = REGION_COORDS.get(r_name, [23.5, 120.5])
        color = get_temp_color(avg_t)
        
        popup_html = f"""
        <div style='font-family: sans-serif; width: 160px;'>
            <h4><b>{r_name}</b></h4>
            <hr style='margin: 4px 0;'>
            <b>📅 日期：</b>{selected_date}<br>
            <b>🌡️ 最低溫：</b>{min_t:.1f} ℃<br>
            <b>🔥 最高溫：</b>{max_t:.1f} ℃<br>
            <b>📊 平均溫：</b>{avg_t:.1f} ℃
        </div>
        """
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{r_name}: {min_t:.0f} ~ {max_t:.0f}℃",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(m, width=900, height=500)

# --- TAB 3: 完整資料庫表 ---
with tab3:
    st.subheader("📋 資料庫實時紀錄庫 (TemperatureForecasts)")
    st.dataframe(df_all[['id', 'locationName', 'regionName', 'dataDate', 'startTime', 'minT', 'maxT', 'weather']], use_container_width=True)

# 頁尾資訊
st.markdown("---")
st.caption("AI 創新微課程 Taiwan Weather Forecast | CWA API × JSON × Python × SQLite × Streamlit × Folium")
