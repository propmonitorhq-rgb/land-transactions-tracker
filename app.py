import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="AI Land Transactions Tracker", layout="wide")
st.title("🇮🇳 AI Land Transactions Tracker")
st.markdown("Automatically tracks land deals from news & X.com • Updated daily")

# ================== LOAD DATA ==================
SHEET_PUBLISH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPj-nFuvFfDAfhl61y5Qgssz6QQEY8RXtPaKBh73nfb0e8253X92pHh_rJ9TqpeOo_YSneo6_qyobA/pub?gid=1727136443&single=true&output=csv"  # ← CHANGE THIS
df = pd.read_csv(SHEET_PUBLISH_URL)
df = df.fillna("")

# Convert date
if "Trans Date" in df.columns:
    df["Trans Date"] = pd.to_datetime(df["Trans Date"], errors="coerce")

# ================== SIDEBAR FILTERS ==================
st.sidebar.header("Filters")
search = st.sidebar.text_input("Search anywhere", "")
cities = st.sidebar.multiselect("City", options=sorted(df["City"].dropna().unique()), default=[])
types = st.sidebar.multiselect("Transaction Type", options=sorted(df["Trns Type"].dropna().unique()), default=[])

# Apply filters
filtered = df.copy()
if search:
    mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
    filtered = filtered[mask]
if cities:
    filtered = filtered[filtered["City"].isin(cities)]
if types:
    filtered = filtered[filtered["Trns Type"].isin(types)]

# Stats
st.metric("Total Transactions", len(filtered))
st.metric("Total Value (₹)", f"₹{filtered['Transaction Value'].astype(str).str.replace(',', '').replace(' Cr','').astype(float).sum():,.0f}" if len(filtered)>0 else "₹0")

# ================== TABLE ==================
cols = ["Description","City","Zoning","Area","Transaction Value","INR Per Sq ft","Trns Type","Trans Date","Property Type","Buyer","Seller","Source Link","Secondary Link"]
column_config = {
    "Source Link": st.column_config.LinkColumn("Source Link"),
    "Secondary Link": st.column_config.LinkColumn("Secondary Link"),
}
st.dataframe(filtered[cols], use_container_width=True, column_config=column_config, hide_index=True)

# ================== MAP ==================
st.header("Transaction Map")
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB positron")
added = False
for _, row in filtered.iterrows():
    if row.get("Location Coordinates"):
        try:
            lat, lon = [float(x.strip()) for x in str(row["Location Coordinates"]).split(",")]
            popup_html = f"""
            <b>{row['Description']}</b><br>
            City: {row['City']}<br>
            Value: ₹{row['Transaction Value']}<br>
            <a href="{row['Source Link']}" target="_blank">Source</a>
            """
            folium.Marker([lat, lon], popup=folium.Popup(popup_html, max_width=300)).add_to(m)
            added = True
        except:
            pass

if added:
    st_folium(m, width=700, height=500)
else:
    st.info("No coordinates available yet – add some in the sheet!")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
