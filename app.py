import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="PropMonitor", layout="wide", initial_sidebar_state="collapsed")

# === EXACT DARK PROP MONITOR UI (copied from your screenshot) ===
st.markdown("""
<style>
    .main {background-color: #0a0a0a; color: #ffffff;}
    .stApp {background-color: #0a0a0a;}
    h1 {font-size: 2.8rem !important; font-weight: 700; margin-bottom: 0 !important; color: #ffffff;}
    .subtitle {font-size: 1.1rem; color: #aaaaaa; margin-bottom: 20px;}
    
    /* Tabs - exact style from screenshot */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0a0a0a;
        border-bottom: 2px solid #222222;
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #cccccc;
        font-size: 18px;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff;
        border-bottom: 4px solid #ef4444;  /* red accent like your screenshot highlight */
        background-color: #0a0a0a;
    }
    
    .stMetric {background: #111111; border-radius: 12px; box-shadow: none;}
    .stDataFrame {border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

# Header - exact match to your screenshot
st.markdown("<h1>PropMonitor</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time land transaction intelligence across India</p>', unsafe_allow_html=True)

# ================== YOUR GOOGLE SHEET URL ==================
SHEET_PUBLISH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPj-nFuvFfDAfhl61y5Qgssz6QQEY8RXtPaKBh73nfb0e8253X92pHh_rJ9TqpeOo_YSneo6_qyobA/pub?output=csv"  
# ← Replace with your real publish link

df = pd.read_csv(SHEET_PUBLISH_URL)
df = df.fillna("")
if "Trans Date" in df.columns:
    df["Trans Date"] = pd.to_datetime(df["Trans Date"], errors="coerce")

# Filters in sidebar (collapsed by default to match clean screenshot look)
with st.sidebar:
    st.header("🔍 Filters")
    search = st.text_input("Search anywhere", "")
    cities = st.multiselect("City", options=sorted(df["City"].dropna().unique()) if "City" in df.columns else [], default=[])
    types = st.multiselect("Transaction Type", options=sorted(df["Trns Type"].dropna().unique()) if "Trns Type" in df.columns else [], default=[])

# Apply filters
filtered = df.copy()
if search:
    mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
    filtered = filtered[mask]
if cities:
    filtered = filtered[filtered["City"].isin(cities)]
if types:
    filtered = filtered[filtered["Trns Type"].isin(types)]

# ================== TABS (positioned exactly under header like your screenshot) ==================
tab_map, tab_feed, tab_analytics = st.tabs(["📍 Map View", "📜 Feed", "📊 Analytics"])

with tab_map:
    st.header("Map View")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="OpenStreetMap")
    added = False
    if "Location Coordinates" in filtered.columns:
        for _, row in filtered.iterrows():
            if row.get("Location Coordinates"):
                try:
                    lat, lon = [float(x.strip()) for x in str(row["Location Coordinates"]).split(",")]
                    popup_html = f"""
                    <b>{row.get('Description', '')}</b><br>
                    City: {row.get('City', '')}<br>
                    Value: ₹{row.get('Transaction Value', '')}<br>
                    Source: {row.get('Source', '')} <a href="{row.get('Link', '')}" target="_blank">[Open]</a>
                    """
                    folium.CircleMarker(
                        [lat, lon],
                        radius=9,
                        color="#22c55e",
                        fill=True,
                        fill_color="#22c55e",
                        fill_opacity=0.95,
                        popup=folium.Popup(popup_html, max_width=300)
                    ).add_to(m)
                    added = True
                except:
                    pass
    if added:
        st_folium(m, width="100%", height=720, returned_objects=[])
    else:
        st.info("Add Location Coordinates (lat,lon) in your Google Sheet to see green markers")

with tab_feed:
    st.header("Feed")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Transactions", len(filtered))
    with c2:
        try:
            clean_val = filtered["Transaction Value"].astype(str).str.replace(',', '').str.replace(' Cr', '').astype(float).sum()
            st.metric("Total Value (₹)", f"₹{clean_val:,.0f}")
        except:
            st.metric("Total Value (₹)", "₹0")
    
    display_cols = ["Description","City","Zoning","Area","Transaction Value","INR Per Sq ft","Trns Type","Trans Date","Property Type","Buyer","Seller","Source","Link","Secondary Link"]
    safe_cols = [col for col in display_cols if col in filtered.columns]
    column_config = {}
    if "Link" in filtered.columns: column_config["Link"] = st.column_config.LinkColumn("Link")
    if "Secondary Link" in filtered.columns: column_config["Secondary Link"] = st.column_config.LinkColumn("Secondary Link")
    
    st.dataframe(filtered[safe_cols], use_container_width=True, column_config=column_config, hide_index=True)

with tab_analytics:
    st.header("Analytics")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Transactions", len(filtered))
    with c2:
        try:
            clean_val = filtered["Transaction Value"].astype(str).str.replace(',', '').str.replace(' Cr', '').astype(float).sum()
            st.metric("Total Value (₹)", f"₹{clean_val:,.0f}")
        except:
            st.metric("Total Value (₹)", "₹0")
    
    if not filtered.empty and "City" in filtered.columns:
        st.subheader("Transactions by City")
        st.bar_chart(filtered["City"].value_counts())

st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %H:%M IST')}")
