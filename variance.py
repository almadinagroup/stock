import streamlit as st
import pandas as pd

# ------------------------
# Page config
# ------------------------
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ------------------------
# Google Sheet CSV URLs (public)
# ------------------------
URL_STOCK = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=0"
URL_NEW   = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=419749881"

CATEGORY_COLUMN = "Category"
COST_COLUMN = "cost"
COST_COLUMN_FOUND = "internal_cost"

# ------------------------
# Function to load a sheet
# ------------------------
@st.cache_data(ttl=600)
def load_sheet(url):
    try:
        df = pd.read_csv(url)
        # Clean columns
        df.columns = df.columns.str.strip()
        # Standardize cost column
        cost_col_match = [c for c in df.columns if c.strip().lower() == COST_COLUMN]
        if cost_col_match:
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            df[COST_COLUMN_FOUND] = pd.NA
        # Ensure Category column exists
        if CATEGORY_COLUMN not in df.columns:
            df[CATEGORY_COLUMN] = "Uncategorized"
        return df
    except Exception as e:
        st.error(f"Error loading sheet from URL {url}: {e}")
        return pd.DataFrame()

# ------------------------
# Load worksheets
# ------------------------
stock_df = load_sheet(URL_STOCK)
new_df   = load_sheet(URL_NEW)

# ------------------------
# Display in Streamlit
# ------------------------
st.title("📦 Inventory Dashboard")

st.subheader("🏬 Warehouse Stock")
st.dataframe(stock_df, use_container_width=True)

st.subheader("🆕 New Arrival")
st.dataframe(new_df, use_container_width=True)
