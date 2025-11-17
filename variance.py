import streamlit as st
import pandas as pd
import gspread # New import
import google.auth # New import
from io import StringIO # Needed for reading gspread data into pandas

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ==========================================
# GOOGLE SHEETS CONFIGURATION
# ==========================================
# ⚠️ 1. Set the Spreadsheet ID (the long string in the URL).
SINGLE_SHEET_ID = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/edit?gid=0#gid=0" # <-- UPDATE THIS ID

# ⚠️ 2. Configure the specific WORKSHEET (tab) name within that sheet.
GSHEETS_CONFIG = {
    "warehouse_stock": {
        "worksheet_name": "stock",
        "date": "2025-10-29"
    },
    "new_arrival": {
        "worksheet_name": "new",
        "date": "2025-10-29"
    }
}

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
CATEGORY_COLUMN = "Category"
COST_COLUMN = "cost"
COST_COLUMN_FOUND = "internal_cost"


# ==========================================
# LOAD DATA FUNCTION (USING GSPREAD)
# ==========================================
@st.cache_data(ttl=600) # Cache the data for 10 minutes
def load_gsheet_gspread(data_label, worksheet_name):
    """
    Loads data from the specified worksheet using the gspread library.
    
    The service account credentials must be defined in st.secrets, 
    matching the standard Streamlit format: st.secrets["gcp_service_account"].
    """
    try:
        # --- Authentication and Client Setup ---
        
        # 1. Load credentials from Streamlit secrets (assuming service account setup)
        # Note: We structure the credentials in a way that gspread/google-auth expects.
        creds_info = st.secrets["gcp_service_account"]
        
        # 2. Authorize gspread client
        gc = gspread.service_account_from_dict(creds_info)
        
        # 3. Open the main spreadsheet by ID
        spreadsheet = gc.open_by_key(SINGLE_SHEET_ID)
        
        # 4. Select the specific worksheet (tab) by name
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # 5. Get all data as a list of lists
        data = worksheet.get_all_values()
        
        # 6. Convert to DataFrame (using the first row as headers)
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # --- Data Cleaning and Standardization (Same as before) ---
        original_cols = df.columns.tolist()
        df.columns = df.columns.str.strip()
        
        cost_col_match = [col for col in original_cols if col.strip().lower() == COST_COLUMN]
        
        if cost_col_match:
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            df[COST_COLUMN_FOUND] = pd.NA
            
        if CATEGORY_COLUMN not in df.columns:
            df[CATEGORY_COLUMN] = "Uncategorized"

        df = df.dropna(how='all')

        return df
    
    except Exception as e:
        st.error(f"❌ Error loading {data_label} from worksheet '{worksheet_name}' using gspread. "
                 f"Please check the Sheet ID, worksheet name, and confirm 'gcp_service_account' is set in secrets. "
                 f"Error detail: {e}")
        return pd.DataFrame()

# ==========================================
# READ BOTH SHEETS (Calling the gspread function)
# ==========================================
stock_df = load_gsheet_gspread(
    "Warehouse Stock", 
    GSHEETS_CONFIG["warehouse_stock"]["worksheet_name"]
)
arrival_df = load_gsheet_gspread(
    "New Arrival", 
    GSHEETS_CONFIG["new_arrival"]["worksheet_name"]
)

# ==========================================
# DATA STRUCTURE (for internal use)
# ==========================================
data = {
    "stock": {
        "data": stock_df,
        "date": GSHEETS_CONFIG["warehouse_stock"]["date"]
    },
    "new_arrival": {
        "data": arrival_df,
        "date": GSHEETS_CONFIG["new_arrival"]["date"]
    }
}


# ==========================================
# HELPER FUNCTION FOR DISPLAY FORMATTING
# ==========================================
def create_overview_df(df, show_cost_in_table=False):
    """
    Creates a copy of the DataFrame for the main table overview.
    Drops the Category column and conditionally drops the standardized cost column.
    """
    if df.empty:
        return pd.DataFrame()
        
    df_display = df.copy()

    # 1. Drop the sensitive COST_COLUMN_FOUND if we are NOT showing it
    if not show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.drop(columns=[COST_COLUMN_FOUND])
    
    # 2. Rename the standardized cost column for display if it's being shown
    elif show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.rename(columns={COST_COLUMN_FOUND: COST_COLUMN.upper()})

    # 3. Drop Category Column (Requested by user)
    if CATEGORY_COLUMN in df_display.columns:
        df_display = df_display.drop(columns=[CATEGORY_COLUMN])
        
    return df_display


# ==========================================
# SIDEBAR FILTERING (Unmodified)
# ==========================================
st.sidebar.title("Filter Options")

# --- Category Filter Logic ---
if CATEGORY_COLUMN in stock_df.columns and CATEGORY_COLUMN in arrival_df.columns:
    all_categories = pd.concat([
        stock_df[CATEGORY_COLUMN].dropna().astype(str),
        arrival_df[CATEGORY_COLUMN].dropna().astype(str)
    ]).str.strip().unique().tolist()
    all_categories.sort()
    all_categories.insert(0, "All Categories")

    selected_category = st.sidebar.selectbox(
        "Select Inventory Category", 
        all_categories,
        index=0
    )
    
    if selected_category != "All Categories":
        filtered_stock_df = stock_df[stock_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category.strip()]
        filtered_arrival_df = arrival_df[arrival_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category.strip()]
    else:
        filtered_stock_df = stock_df
        filtered_arrival_df = arrival_df

else:
    st.sidebar.warning(f"⚠️ Cannot find '{CATEGORY_COLUMN}' column. Displaying unfiltered data.")
    selected_category = "All Categories"
    filtered_stock_df = stock_df
    filtered_arrival_df = arrival_df


# ==========================================
# COMMON SEARCH BAR (TOP)
# ==========================================
st.title("📦 Inventory Dashboard")
st.markdown("---")

# Global CSS (Download button hiding remains)
st.markdown("""
<style>
/* Center the tabs for better mobile viewing */
.stTabs [data-baseweb="tab-list"] {
    justify-content: center;
    margin-bottom: 20px;
}
/* 🎯 AGGRESSIVE DOWNLOAD BUTTON HIDING 🎯 */
[data-testid="stDownloadButton"],
[data-testid^="stDataFrameToolbar"] > div:nth-child(2) {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

query = st.text_input(
    "🔍 Search for Item Name or Barcode across all inventory:", 
    placeholder="Enter Barcode or Item Description here...",
    label_visibility="visible"
).strip().lower()

# ==========================================
# SEARCH LOGIC AND DISPLAY (COST IS VISIBLE HERE)
# ==========================================
if query:
    st.subheader(f"Search Results for: **'{query}'**")
    
    def search_df(df, query):
        if df.empty:
            return pd.DataFrame()
        return df[
            df.apply(lambda row: query in str(row.get("itembarcode", "")).lower() or
                                 query in str(row.get("description", "")).lower(), axis=1)
        ]

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
        st.warning(f"❌ No matching items found for **'{query}'** in either dataset.")
        
# ==========================================
# TABBED PAGE VIEWS (If no search query is active) (COST IS HIDDEN HERE)
# ==========================================
else:
    filter_status = f"({f'Filtered by **{selected_category}**' if selected_category != 'All Categories' else 'All Stock'})"

    tab1, tab2 = st.tabs(["🏬 Warehouse Stock", "🆕 New Arrival"])
    
    with tab1:
        st.subheader("🏬 Warehouse Stock")
        st.write(f"📅 Last Updated: **{data['stock']['date']}** {filter_status}")

        if not filtered_stock_df.empty:
            stock_overview_df = create_overview_df(filtered_stock_df, show_cost_in_table=False)
            st.dataframe(stock_overview_df, use_container_width=True)
            
        elif not stock_df.empty:
            st.info(f"No items found in Warehouse Stock for category: **{selected_category}**.")
        else:
            st.warning(f"⚠️ Could not display data from Spreadsheet ID **{SINGLE_SHEET_ID}** (Worksheet: '{GSHEETS_CONFIG['warehouse_stock']['worksheet_name']}').")

    with tab2:
        st.subheader("🆕 New Arrival")
        st.write(f"📅 Last Updated: **{data['new_arrival']['date']}** {filter_status}")

        if not filtered_arrival_df.empty:
            arrival_overview_df = create_overview_df(filtered_arrival_df, show_cost_in_table=False)
            st.dataframe(arrival_overview_df, use_container_width=True)
            
        elif not arrival_df.empty:
            st.info(f"No items found in New Arrivals for category: **{selected_category}**.")
        else:
            st.warning(f"⚠️ Could not display data from Spreadsheet ID **{SINGLE_SHEET_ID}** (Worksheet: '{GSHEETS_CONFIG['new_arrival']['worksheet_name']}').")
