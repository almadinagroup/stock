import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ------------------------
# Page config
# ------------------------
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ------------------------
# Google Sheets setup
# ------------------------
SHEET_ID = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/edit?gid=0#gid=0"

WORKSHEETS = {
    "stock": "stock",
    "new": "new"
}

CATEGORY_COLUMN = "Category"
COST_COLUMN = "cost"
COST_COLUMN_FOUND = "internal_cost"

# ------------------------
# Load sheet function (with proper scopes)
# ------------------------
@st.cache_data(ttl=600)
def load_sheet(worksheet_name):
    try:
        # Define scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Load credentials from Streamlit secrets
        creds_info = st.secrets["google_service_account"]
        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)

        # Authorize gspread
        gc = gspread.authorize(credentials)

        # Open sheet and get worksheet
        sheet = gc.open_by_key(SHEET_ID)
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])

        # Clean columns
        df.columns = df.columns.str.strip()
        cost_col_match = [c for c in df.columns if c.strip().lower() == COST_COLUMN]
        if cost_col_match:
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            df[COST_COLUMN_FOUND] = pd.NA
        if CATEGORY_COLUMN not in df.columns:
            df[CATEGORY_COLUMN] = "Uncategorized"

        df = df.dropna(how='all')
        return df

    except Exception as e:
        st.error(f"Error loading {worksheet_name}: {e}")
        return pd.DataFrame()

# ------------------------
# Load both worksheets
# ------------------------
stock_df = load_sheet(WORKSHEETS["stock"])
new_df = load_sheet(WORKSHEETS["new"])

# ------------------------
# Display in Streamlit
# ------------------------
st.title("📦 Inventory Dashboard")
st.subheader("🏬 Warehouse Stock")
st.dataframe(stock_df, use_container_width=True)

st.subheader("🆕 New Arrival")
st.dataframe(new_df, use_container_width=True)
