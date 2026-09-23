"""
app.py - Taiwan Weather Forecast Pro (全彩高清版)
整合 7 天預報 + OpenStreetMap 全彩高清地圖 + AI 氣象主播廣播文案 + 戶外旅遊指數 + 全台氣溫排行榜。
"""

import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from database import sync_api_to_db, get_all_forecasts_df, init_db
from ai_presenter import generate_weather_script, assess_travel_suitability, get_extreme_weather_alerts

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast Pro",
    page_icon="🌤️",
    layout="wide"
)

# 初始化資料庫
init_db()

# 6 大分區座標
REGION_COORDS = {
    "北部地區": [25.0330, 121.5654],
    "中部地區": [24.1477, 120.6736],
    "南部地區": [22.6273, 120.3014],
    "東部地區": [23.9871, 121.6015],
    "東北部地區": [24.7570, 121.7530],
    "東南部地區": [22.7583, 121.1444],
    "離島地區": [23.5711, 119.5793]
}

# 22 縣市座標
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

def get_temp_color_hex(temp: float) -> str:
    """依據溫度傳回 Hex 色碼"""
    if temp < 20:
        return "#1C83E1"       # <20℃ 寶藍色
    elif temp <= 25:
        return "#2E7D32"      # 20-25℃ 森林綠
    elif temp <= 30:
        return "#EF6C00"      # 25-30℃ 鮮橘色
    else:
        return "#D32F2F"      # >30℃ 亮紅色

# 標題
st.title("🌤️ Taiwan Weather Forecast 7 天氣象互動儀表板 Pro")
st.markdown("##### *用程式探索天氣 · 用資料看見台灣 · 用 AI 實現更多可能*")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 控制與設定")
    if st.button("🔄 同步最新 7 天 CWA 氣象資料"):
        with st.spinner("正在向中央氣象署抓取最新預報..."):
            count = sync_api_to_db()
            st.success(f"成功同步 {count} 筆氣象資料！")
            st.rerun()

    st.markdown("---")
    df_all = get_all_forecasts_df()
    
    if df_all.empty:
        st.warning("資料庫尚無資料，請點擊上方按鈕進行同步。")
        st.stop()
        
    available_regions = list(df_all["regionName"].unique())
    selected_region = st.selectbox("🎯 選擇觀測地區 (Region)", available_regions)

    available_dates = sorted(df_all["dataDate"].unique())
    selected_date = st.selectbox("📅 選擇觀測日期 (Select Date)", available_dates)

    st.markdown("---")
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載 7 天完整氣象 CSV",
        data=csv_data,
        file_name=f"Taiwan_7Day_Weather_Forecast.csv",
        mime="text/csv"
    )

# 頂部 KPI 列
df_today = df_all[df_all["dataDate"] == selected_date]
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

if not df_today.empty:
    max_t_all = df_today["maxT"].max()
    min_t_all = df_today["minT"].min()
    avg_pop_all = df_today["pop"].mean()
    total_dates = len(available_dates)
    total_count = len(df_all)
    
    col_m1.metric("🔥 當日最高溫", f"{max_t_all:.1f} °C")
    col_m2.metric("🧊 當日最低溫", f"{min_t_all:.1f} °C")
    col_m3.metric("🌧️ 平均降雨率", f"{avg_pop_all:.0f} %")
    col_m4.metric("📅 預報天數", f"{total_dates} 天完整預報")
    col_m5.metric("📊 總資料庫筆數", f"{total_count} 筆")
st.markdown("---")

# 四大頁籤
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 7 天溫差趨勢與建議", 
    "🗺️ 高清晰全台氣溫地圖", 
    "🎙️ AI 氣象主播與旅遊顧問", 
    "📋 7 天氣象資料庫清單"
])

# --- TAB 1: 7天趨勢與建議 ---
with tab1:
    st.subheader(f"📍 {selected_region} - 7 天一週最高/最低氣溫趨勢")
    
    df_region = df_all[df_all["regionName"] == selected_region].copy()
    
    reg_max = df_region["maxT"].max()
    reg_min = df_region["minT"].min()
    reg_pop = df_region["pop"].max()
    reg_wx = df_region["weather"].iloc[0] if not df_region.empty else "多雲"
    reg_ci = df_region["ci"].iloc[0] if "ci" in df_region.columns else "舒適"
    
    c_alert1, c_alert2 = st.columns(2)
    with c_alert1:
        if reg_max >= 30:
            st.error(f"🚨 **高溫注意**：一週最高溫達 {reg_max:.0f}°C！請注意防曬補充水分。")
        elif reg_min <= 20:
            st.info(f"🧥 **保暖提醒**：一週最低溫降至 {reg_min:.0f}°C，建議攜帶外套。")
        else:
            st.success(f"☀️ **體感舒適**：平均氣溫約 {(reg_max+reg_min)/2:.1f}°C，預報體感【{reg_ci}】。")
            
    with c_alert2:
        if reg_pop >= 30:
            st.warning(f"🌧️ **降雨預警**：最高降雨機率達 {reg_pop}%！請隨身攜帶雨具。")
        else:
            st.success(f"🌤️ **天氣穩定**：最高降雨機率僅 {reg_pop}%，相當適合戶外行程。")

    st.markdown("#### 💡 7 天穿搭建議")
    st.info(f"**建議穿搭**：{selected_region} 天氣以「{reg_wx}」為主，舒適度【{reg_ci}】。建議洋蔥式穿法隨時調整。")

    st.markdown("---")
    
    df_chart = df_region.groupby("dataDate").agg(
        MinT=("minT", "min"),
        MaxT=("maxT", "max"),
        PoP=("pop", "max")
    ).reset_index()
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown("##### 📈 7 天溫差趨勢圖 (MaxT vs MinT)")
        st.line_chart(df_chart.set_index("dataDate")[["MaxT", "MinT"]], color=["#D32F2F", "#1C83E1"])
        
    with col_c2:
        st.markdown("##### 📝 一週每日數據表格")
        st.dataframe(
            df_chart.rename(columns={"dataDate":"預報日期", "MinT":"最低溫(°C)", "MaxT":"最高溫(°C)", "PoP":"降雨率(%)"}),
            use_container_width=True
        )

# --- TAB 2: 高清晰地圖 (使用 OpenStreetMap 全彩高清標準底圖) ---
with tab2:
    st.subheader(f"🗺️ 全台氣溫與天氣地圖 (預報日期：{selected_date})")
    
    map_mode = st.radio("🔍 地圖模式：", ["全台 22 縣市視角 (直觀數據標籤)", "6 大區域視角 (區域統計)"], horizontal=True)
    
    df_date = df_all[df_all["dataDate"] == selected_date]
    # 固定為 OpenStreetMap 全彩高清標準底圖
    m = folium.Map(location=[23.7, 120.95], zoom_start=8, tiles="OpenStreetMap")
    
    if map_mode == "全台 22 縣市視角 (直觀數據標籤)":
        city_summary = df_date.groupby("locationName").agg(
            minT=("minT", "min"),
            maxT=("maxT", "max"),
            pop=("pop", "max"),
            weather=("weather", "first")
        ).reset_index()
        
        for _, row in city_summary.iterrows():
            c_name = row["locationName"]
            min_t, max_t, pop, wx = row["minT"], row["maxT"], row["pop"], row["weather"]
            avg_t = (min_t + max_t) / 2.0
            coords = CITY_COORDS.get(c_name, [23.5, 120.5])
            color_hex = get_temp_color_hex(avg_t)
            
            folium.CircleMarker(
                location=coords,
                radius=18,
                color=color_hex,
                fill=True,
                fill_color=color_hex,
                fill_opacity=0.35,
                weight=2
            ).add_to(m)
            
            icon_html = f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid {color_hex};
                border-radius: 8px;
                padding: 3px 6px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-family: Microsoft JhengHei, sans-serif;
                white-space: nowrap;
                text-align: center;
                line-height: 1.3;
            ">
                <div style="font-weight: bold; font-size: 12px; color: #111;">{c_name}</div>
                <div style="font-weight: bold; font-size: 13px; color: {color_hex};">{min_t:.0f}° ~ {max_t:.0f}°C</div>
                <div style="font-size: 10px; color: #555;">{wx} | 🌧️{pop}%</div>
            </div>
            """
            
            folium.Marker(
                location=coords,
                icon=folium.DivIcon(html=icon_html, icon_anchor=(45, 20))
            ).add_to(m)
            
    else:
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
            color_hex = get_temp_color_hex(avg_t)
            
            folium.CircleMarker(
                location=coords,
                radius=32,
                color=color_hex,
                fill=True,
                fill_color=color_hex,
                fill_opacity=0.3,
                weight=3
            ).add_to(m)
            
            icon_html = f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid {color_hex};
                border-radius: 10px;
                padding: 6px 10px;
                box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
                font-family: Microsoft JhengHei, sans-serif;
                white-space: nowrap;
                text-align: center;
            ">
                <div style="font-weight: bold; font-size: 14px; color: #111;">📍 {r_name}</div>
                <div style="font-weight: bold; font-size: 15px; color: {color_hex};">{min_t:.0f}° ~ {max_t:.0f}°C</div>
                <div style="font-size: 11px; color: #444;">平均 {avg_t:.1f}°C | 降雨 {pop}%</div>
            </div>
            """
            folium.Marker(
                location=coords,
                icon=folium.DivIcon(html=icon_html, icon_anchor=(55, 25))
            ).add_to(m)

    st_folium(m, width=1000, height=600)

# --- TAB 3: AI 氣象主播與旅遊顧問 ---
with tab3:
    st.subheader("🎙️ AI 氣象主播廣播文案 & 戶外旅遊適合度評估")
    
    col_ai1, col_ai2 = st.columns([3, 2])
    
    with col_ai1:
        st.markdown("### 🎙️ 新聞級 AI 氣象廣播文案")
        df_selected_reg = df_all[df_all["regionName"] == selected_region]
        script_text = generate_weather_script(selected_region, df_selected_reg)
        
        st.text_area("廣播口播稿內容 (可複製使用)：", script_text, height=320)
        
    with col_ai2:
        st.markdown("### 🧳 戶外旅遊適合度評估")
        travel_info = assess_travel_suitability(selected_region, df_selected_reg)
        
        st.metric("旅遊指數評分", f"{travel_info['score']} / 100", delta=travel_info['status'])
        st.markdown(f"**最佳出遊時段**：{travel_info['best_time']}")
        st.markdown(f"**建議指引**：{travel_info['advice']}")

    st.markdown("---")
    
    st.markdown("### 🚨 全台 7 天極端天氣與氣溫排行榜")
    c_rank1, c_rank2 = st.columns(2)
    
    with c_rank1:
        st.markdown("##### 🏆 當日全台最高溫 Top 3 縣市")
        df_top_heat = df_today.groupby("locationName")["maxT"].max().reset_index().sort_values(by="maxT", ascending=False).head(3)
        st.dataframe(df_top_heat.rename(columns={"locationName":"縣市", "maxT":"最高溫(°C)"}), use_container_width=True)
        
    with c_rank2:
        st.markdown("##### ❄️ 當日全台最涼爽 Top 3 縣市")
        df_top_cool = df_today.groupby("locationName")["minT"].min().reset_index().sort_values(by="minT", ascending=True).head(3)
        st.dataframe(df_top_cool.rename(columns={"locationName":"縣市", "minT":"最低溫(°C)"}), use_container_width=True)

# --- TAB 4: 7天資料庫 ---
with tab4:
    st.subheader("📋 7 天預報完整資料庫清單 (TemperatureForecasts)")
    st.dataframe(
        df_all[['id', 'locationName', 'regionName', 'dataDate', 'startTime', 'minT', 'maxT', 'weather', 'pop', 'ci']],
        use_container_width=True
    )

# 頁尾
st.markdown("---")
st.caption("AI 創新微課程 Taiwan Weather Forecast Pro | 7-Day CWA Open Data API (F-D0047-091) × SQLite × Streamlit × Folium OpenStreetMap")
