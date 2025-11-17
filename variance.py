import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ==========================================
# GOOGLE SHEETS CONFIGURATION
# ==========================================
SINGLE_SHEET_ID = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/edit?gid=0#gid=0"  # <-- Update this

GSHEETS_CONFIG = {
    "warehouse_stock": {"worksheet_name": "stock", "date": "2025-10-29"},
    "new_arrival": {"worksheet_name": "new", "date": "2025-10-29"}
}

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
CATEGORY_COLUMN = "Category"
COST_COLUMN = "cost"
COST_COLUMN_FOUND = "internal_cost"

# ==========================================
# LOAD DATA FUNCTION (USING GSPREAD + SERVICE ACCOUNT)
# ==========================================
@st.cache_data(ttl=600)
def load_gsheet_gspread(data_label, worksheet_name):
    """
    Loads data from Google Sheets using gspread with Streamlit Cloud secrets.
    """
    try:
        # --- Use service account from Streamlit secrets ---
        creds_info = st.secrets["google_service_account"]
        credentials = Credentials.from_service_account_info(creds_info)
        gc = gspread.authorize(credentials)
        
        # Open spreadsheet and worksheet
        spreadsheet = gc.open_by_key(SINGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Fetch all data and convert to DataFrame
        data = worksheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Clean columns
        df.columns = df.columns.str.strip()
        cost_col_match = [col for col in df.columns if col.strip().lower() == COST_COLUMN]
        if cost_col_match:
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            df[COST_COLUMN_FOUND] = pd.NA
        
        if CATEGORY_COLUMN not in df.columns:
            df[CATEGORY_COLUMN] = "Uncategorized"
        
        df = df.dropna(how='all')
        return df

    except Exception as e:
        st.error(f"❌ Error loading {data_label} from worksheet '{worksheet_name}'. {e}")
        return pd.DataFrame()

# ==========================================
# LOAD DATA
# ==========================================
stock_df = load_gsheet_gspread("Warehouse Stock", GSHEETS_CONFIG["warehouse_stock"]["worksheet_name"])
arrival_df = load_gsheet_gspread("New Arrival", GSHEETS_CONFIG["new_arrival"]["worksheet_name"])

data = {
    "stock": {"data": stock_df, "date": GSHEETS_CONFIG["warehouse_stock"]["date"]},
    "new_arrival": {"data": arrival_df, "date": GSHEETS_CONFIG["new_arrival"]["date"]}
}

# ==========================================
# HELPER FUNCTION
# ==========================================
def create_overview_df(df, show_cost_in_table=False):
    if df.empty:
        return pd.DataFrame()
    df_display = df.copy()
    if not show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.drop(columns=[COST_COLUMN_FOUND])
    elif show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.rename(columns={COST_COLUMN_FOUND: COST_COLUMN.upper()})
    if CATEGORY_COLUMN in df_display.columns:
        df_display = df_display.drop(columns=[CATEGORY_COLUMN])
    return df_display

# ==========================================
# SIDEBAR FILTER
# ==========================================
st.sidebar.title("Filter Options")

if CATEGORY_COLUMN in stock_df.columns and CATEGORY_COLUMN in arrival_df.columns:
    all_categories = pd.concat([stock_df[CATEGORY_COLUMN].dropna(), arrival_df[CATEGORY_COLUMN].dropna()]).str.strip().unique().tolist()
    all_categories.sort()
    all_categories.insert(0, "All Categories")
    selected_category = st.sidebar.selectbox("Select Inventory Category", all_categories, index=0)
    
    if selected_category != "All Categories":
        filtered_stock_df = stock_df[stock_df[CATEGORY_COLUMN].str.strip() == selected_category]
        filtered_arrival_df = arrival_df[arrival_df[CATEGORY_COLUMN].str.strip() == selected_category]
    else:
        filtered_stock_df = stock_df
        filtered_arrival_df = arrival_df
else:
    st.sidebar.warning(f"⚠️ Cannot find '{CATEGORY_COLUMN}' column. Displaying unfiltered data.")
    selected_category = "All Categories"
    filtered_stock_df = stock_df
    filtered_arrival_df = arrival_df

# ==========================================
# SEARCH BAR
# ==========================================
st.title("📦 Inventory Dashboard")
st.markdown("---")
query = st.text_input("🔍 Search for Item Name or Barcode across all inventory:").strip().lower()

if query:
    st.subheader(f"Search Results for: '{query}'")
    def search_df(df, query):
        if df.empty:
            return pd.DataFrame()
        return df[df.apply(lambda r: query in str(r.get("itembarcode", "")).lower() or query in str(r.get("description", "")).lower(), axis=1)]
    
    results_stock = search_df(stock_df, query)
    results_arrival = search_df(arrival_df, query)

    if not results_stock.empty or not results_arrival.empty:
        if not results_stock.empty:
            st.markdown("### 🏬 Found in Warehouse Stock")
            st.dataframe(create_overview_df(results_stock, show_cost_in_table=True), use_container_width=True)
        if not results_arrival.empty:
            st.markdown("### 🆕 Found in New Arrivals")
            st.dataframe(create_overview_df(results_arrival, show_cost_in_table=True), use_container_width=True)
    else:
        st.warning(f"No matching items found for '{query}' in either dataset.")
else:
    filter_status = f"({f'Filtered by {selected_category}' if selected_category != 'All Categories' else 'All Stock'})"
    tab1, tab2 = st.tabs(["🏬 Warehouse Stock", "🆕 New Arrival"])
    
    with tab1:
        st.subheader("🏬 Warehouse Stock")
        st.write(f"📅 Last Updated: {data['stock']['date']} {filter_status}")
        st.dataframe(create_overview_df(filtered_stock_df), use_container_width=True)
    
    with tab2:
        st.subheader("🆕 New Arrival")
        st.write(f"📅 Last Updated: {data['new_arrival']['date']} {filter_status}")
        st.dataframe(create_overview_df(filtered_arrival_df), use_container_width=True)
