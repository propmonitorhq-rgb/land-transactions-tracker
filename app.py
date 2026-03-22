import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="AI Land Transactions Tracker", layout="wide")
st.title("🇮🇳 AI Land Transactions Tracker")
st.markdown("Automatically tracks land deals from news & X.com • Updated daily")

# ================== CHANGE THIS ==================
SHEET_PUBLISH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPj-nFuvFfDAfhl61y5Qgssz6QQEY8RXtPaKBh73nfb0e8253X92pHh_rJ9TqpeOo_YSneo6_qyobA/pub?output=csv"  
# ← Paste the FULL link you copied above (replace the entire line)

# ================== LOAD DATA WITH FRIENDLY ERROR ==================
try:
    df = pd.read_csv(SHEET_PUBLISH_URL)
    df = df.fillna("")
except Exception as e:
    st.error("❌ Could not load your Google Sheet!\n\n"
             "Please follow Step 1 above and paste the FULL publish URL in app.py")
    st.caption("Tip: The URL must end with /pub?output=csv and the sheet must be published as CSV.")
    st.stop()

# Convert date safely
if "Trans Date" in df.columns:
    df["Trans Date"] = pd.to_datetime(df["Trans Date"], errors="coerce")

# ================== DEBUG (will disappear once working) ==================
st.subheader("🔍 Debug: Columns loaded from Google Sheet")
st.write(df.columns.tolist())

# ================== SIDEBAR FILTERS ==================
st.sidebar.header("Filters")
search = st.sidebar.text_input("Search anywhere", "")
cities = st.sidebar.multiselect("City", options=sorted(df["City"].dropna().unique()) if "City" in df.columns else [], default=[])
types = st.sidebar.multiselect("Transaction Type", options=sorted(df["Trns Type"].dropna().unique()) if "Trns Type" in df.columns else [], default=[])

# Apply filters
filtered = df.copy()
if search:
    mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
    filtered = filtered[mask]
if cities and "City" in filtered.columns:
    filtered = filtered[filtered["City"].isin(cities)]
if types and "Trns Type" in filtered.columns:
    filtered = filtered[filtered["Trns Type"].isin(types)]

# Stats
st.metric("Total Transactions", len(filtered))
value_col = "Transaction Value"
if value_col in filtered.columns:
    try:
        clean = filtered[value_col].astype(str).str.replace(',', '').str.replace(' Cr', '').astype(float)
        st.metric("Total Value (₹)", f"₹{clean.sum():,.0f}")
    except:
        st.metric("Total Value (₹)", "₹0")
else:
    st.metric("Total Value (₹)", "₹0")

# ================== TABLE (matches your exact headers) ==================
display_cols = [
    "Description", "City", "Zoning", "Area", "Transaction Value",
    "INR Per Sq ft", "Trns Type", "Trans Date", "Property Type",
    "Buyer", "Seller", "Source", "Link", "Secondary Link"
]

safe_cols = [col for col in display_cols if col in filtered.columns]

column_config = {}
if "Link" in filtered.columns:
    column_config["Link"] = st.column_config.LinkColumn("Link")
if "Secondary Link" in filtered.columns:
    column_config["Secondary Link"] = st.column_config.LinkColumn("Secondary Link")

if safe_cols:
    st.dataframe(
        filtered[safe_cols],
        use_container_width=True,
        column_config=column_config,
        hide_index=True
    )
else:
    st.dataframe(filtered, use_container_width=True, hide_index=True)

# ================== MAP ==================
st.header("Transaction Map")
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB positron")
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
                Source: {row.get('Source', 'View')} 
                <a href="{row.get('Link', '')}" target="_blank">[Open Link]</a>
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
