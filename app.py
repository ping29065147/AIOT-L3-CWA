"""
app.py - Taiwan Weather Forecast Pro (7天全週極致版)
整合 7 天預報 API + 全彩清晰高清地圖 + 直觀數據標籤卡片 + AI 穿搭建議與 CSV 下載。
"""

import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from database import sync_api_to_db, get_all_forecasts_df, init_db

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast 7-Day Pro",
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
    "臺東縣": [22.7583, 121.1444], "台东縣": [22.7583, 121.1444],
    "澎湖縣": [23.5711, 119.5793], "金門縣": [24.4493, 118.3766], "連江縣": [26.1505, 119.9499]
}

def get_temp_color_hex(temp: float) -> str:
    """依據溫度傳回色碼 Hex"""
    if temp < 20:
        return "#1C83E1"       # <20℃ 寶藍色
    elif temp <= 25:
        return "#2E7D32"      # 20-25℃ 森林綠
    elif temp <= 30:
        return "#EF6C00"      # 25-30℃ 鮮橘色
    else:
        return "#D32F2F"      # >30℃ 亮紅色

# 標題列
st.title("🌤️ Taiwan Weather Forecast 7 天一週天氣預報儀表板")
st.markdown("##### *用程式探索天氣 · 用資料看見台灣 | 全台 22 縣市 7 天氣象觀測與高清晰互動地圖*")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 控制與設定")
    if st.button("🔄 同步最新 7 天 CWA 氣象資料"):
        with st.spinner("正在向中央氣象署抓取未來一週 7 天最新預報..."):
            count = sync_api_to_db()
            st.success(f"成功同步 {count} 筆 7 天氣象資料！")
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
    st.markdown("🗺️ **地圖底圖風格選擇**")
    tile_choice = st.radio("地圖模式：", ["OpenStreetMap (全彩高清標準)", "CartoDB voyager (亮麗現代)", "CartoDB positron (簡約淡色)"])
    
    tiles_map = {
        "OpenStreetMap (全彩高清標準)": "OpenStreetMap",
        "CartoDB voyager (亮麗現代)": "CartoDB voyager",
        "CartoDB positron (簡約淡色)": "CartoDB positron"
    }
    selected_tile = tiles_map[tile_choice]

    st.markdown("---")
    csv_data = df_all.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載 7 天完整氣象 CSV",
        data=csv_data,
        file_name=f"Taiwan_7Day_Weather_Forecast.csv",
        mime="text/csv"
    )

# 頂部 KPI 指標列
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
    col_m4.metric("📅 涵蓋預報天數", f"{total_dates} 天完整預報")
    col_m5.metric("📊 總資料庫筆數", f"{total_count} 筆")
st.markdown("---")

# 主頁籤
tab1, tab2, tab3 = st.tabs(["📊 7 天溫差趨勢與 AI 穿搭建議", "🗺️ 高清晰全台氣溫互動地圖", "📋 7 天氣象資料庫清單"])

# --- TAB 1: 7天趨勢與穿搭建議 ---
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
            st.error(f"🚨 **高溫注意**：一週內最高溫達 {reg_max:.0f}°C！出門請注意防曬、補充水分。")
        elif reg_min <= 20:
            st.info(f"🧥 **保暖提醒**：一週內最低溫降至 {reg_min:.0f}°C，夜間氣溫較低，建議備妥外套。")
        else:
            st.success(f"☀️ **體感舒適**：平均氣溫約 {(reg_max+reg_min)/2:.1f}°C，預報體感為【{reg_ci}】。")
            
    with c_alert2:
        if reg_pop >= 30:
            st.warning(f"🌧️ **降雨機率增加**：本週最高降雨機率達 {reg_pop}%！外出請記得攜帶雨具。")
        else:
            st.success(f"🌤️ **天氣穩定**：最高降雨機率僅 {reg_pop}%，氣候相當適合安排戶外行程！")

    st.markdown("#### 💡 7 天 AI 智慧穿搭與活動建議")
    st.info(f"**綜合建議**：{selected_region} 天氣以「{reg_wx}」為主，舒適度【{reg_ci}】。建議採用洋蔥式穿法，內層短袖配搭外層薄外套，隨時因應晝夜溫差。")

    st.markdown("---")
    
    # 7 天折線圖與表格
    df_chart = df_region.groupby("dataDate").agg(
        MinT=("minT", "min"),
        MaxT=("maxT", "max"),
        PoP=("pop", "max")
    ).reset_index()
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown("##### 📈 7 天一週溫差趨勢圖 (MaxT vs MinT)")
        st.line_chart(df_chart.set_index("dataDate")[["MaxT", "MinT"]], color=["#D32F2F", "#1C83E1"])
        
    with col_c2:
        st.markdown("##### 📝 一週每日數據明細")
        st.dataframe(
            df_chart.rename(columns={"dataDate":"預報日期", "MinT":"最低溫(°C)", "MaxT":"最高溫(°C)", "PoP":"降雨率(%)"}),
            use_container_width=True
        )

# --- TAB 2: 高清晰全台地圖 ---
with tab2:
    st.subheader(f"🗺️ 全台氣溫與天氣地圖 (預報日期：{selected_date})")
    
    map_mode = st.radio("🔍 地圖呈現模式：", ["全台 22 縣市視角 (直觀數據標籤)", "6 大區域視角 (區域統計)"], horizontal=True)
    
    df_date = df_all[df_all["dataDate"] == selected_date]
    
    # 建立高清晰地圖
    m = folium.Map(location=[23.7, 120.95], zoom_start=8, tiles=selected_tile)
    
    if map_mode == "全台 22 縣市視角 (直觀數據標籤)":
        # 依據縣市平均過濾
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
            
            # 添加氣溫半透明色塊半徑圓圈
            folium.CircleMarker(
                location=coords,
                radius=18,
                color=color_hex,
                fill=True,
                fill_color=color_hex,
                fill_opacity=0.35,
                weight=2
            ).add_to(m)
            
            # 直觀白色浮動資訊卡片（免點擊即可直接閱讀文字）
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
            
    else:  # 6 大分區模式
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

# --- TAB 3: 7天資料庫 ---
with tab3:
    st.subheader("📋 7 天預報完整資料庫清單 (TemperatureForecasts)")
    st.dataframe(
        df_all[['id', 'locationName', 'regionName', 'dataDate', 'startTime', 'minT', 'maxT', 'weather', 'pop', 'ci']],
        use_container_width=True
    )

# 頁尾
st.markdown("---")
st.caption("AI 創新微課程 Taiwan Weather Forecast Pro | 7-Day CWA Open Data API (F-D0047-091) × SQLite × Streamlit × Folium")
