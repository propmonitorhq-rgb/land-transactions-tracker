import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="PropMonitor", layout="wide")

# Modern CSS to match the clean PropMonitor look
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    h1 {font-size: 2.2rem; font-weight: 700; color: #111;}
    .stTabs [data-baseweb="tab-list"] button {font-size: 18px; font-weight: 600;}
    .stMetric {background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);}
    .stDataFrame {border-radius: 12px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

# PropMonitor Header (exactly like your screenshot)
st.markdown("<h1 style='margin-bottom:0;'>PropMonitor</h1>", unsafe_allow_html=True)
st.markdown("Real-time land transaction intelligence across India")

# ================== YOUR GOOGLE SHEET URL ==================
SHEET_PUBLISH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPj-nFuvFfDAfhl61y5Qgssz6QQEY8RXtPaKBh73nfb0e8253X92pHh_rJ9TqpeOo_YSneo6_qyobA/pub?output=csv"  
# ← Paste your real /pub?output=csv link here

df = pd.read_csv(SHEET_PUBLISH_URL)
df = df.fillna("")
if "Trans Date" in df.columns:
    df["Trans Date"] = pd.to_datetime(df["Trans Date"], errors="coerce")

# Sidebar Filters (kept for functionality)
st.sidebar.header("Filters")
search = st.sidebar.text_input("Search anywhere", "")
cities = st.sidebar.multiselect("City", options=sorted(df["City"].dropna().unique()) if "City" in df.columns else [], default=[])
types = st.sidebar.multiselect("Transaction Type", options=sorted(df["Trns Type"].dropna().unique()) if "Trns Type" in df.columns else [], default=[])

# Apply filters
filtered = df.copy()
if search:
    mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
    filtered = filtered[mask]
if cities:
    filtered = filtered[filtered["City"].isin(cities)]
if types:
    filtered = filtered[filtered["Trns Type"].isin(types)]

# ================== TABS (exactly like your screenshot) ==================
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
                        location=[lat, lon],
                        radius=10,
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
        st_folium(m, width="100%", height=650)
    else:
        st.info("Add Location Coordinates (lat,lon) in your sheet to see green markers")

with tab_feed:
    st.header("Feed")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", len(filtered))
    with col2:
        try:
            clean = filtered["Transaction Value"].astype(str).str.replace(',', '').str.replace(' Cr', '').astype(float)
            st.metric("Total Value (₹)", f"₹{clean.sum():,.0f}")
        except:
            st.metric("Total Value (₹)", "₹0")
    
    display_cols = ["Description","City","Zoning","Area","Transaction Value","INR Per Sq ft","Trns Type","Trans Date","Property Type","Buyer","Seller","Source","Link","Secondary Link"]
    safe_cols = [col for col in display_cols if col in filtered.columns]
    column_config = {}
    if "Link" in filtered.columns:
        column_config["Link"] = st.column_config.LinkColumn("Link")
    if "Secondary Link" in filtered.columns:
        column_config["Secondary Link"] = st.column_config.LinkColumn("Secondary Link")
    
    st.dataframe(filtered[safe_cols], use_container_width=True, column_config=column_config, hide_index=True)

with tab_analytics:
    st.header("Analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", len(filtered))
    with col2:
        try:
            clean = filtered["Transaction Value"].astype(str).str.replace(',', '').str.replace(' Cr', '').astype(float)
            st.metric("Total Value (₹)", f"₹{clean.sum():,.0f}")
        except:
            st.metric("Total Value (₹)", "₹0")
    
    if not filtered.empty and "City" in filtered.columns:
        st.subheader("Transactions by City")
        st.bar_chart(filtered["City"].value_counts())

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
