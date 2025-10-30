import streamlit as st
import pandas as pd
import numpy as np 

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ==========================================
# MANUAL FILE NAMES AND DATES
# ==========================================
# ⚠️ Make sure both Excel files are in the same folder as this script.
files = {
    "warehouse_stock": {
        "path": "stock ware.xlsx", # UPDATED PATH
        "date": "2025-10-29"
    },
    "new_arrival": {
        "path": "NEW ARRAIVAL-27-OCT-25 (1).xlsx",
        "date": "2025-10-29"
    }
}

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
CATEGORY_COLUMN = "Category" # Column used for sidebar filtering
COST_COLUMN = "cost"         # The sensitive column (used for matching, case-insensitive)
COST_COLUMN_FOUND = "internal_cost" # Internal standardized name for the sensitive column


# ==========================================
# LOAD DATA FUNCTION (MODIFIED TO SILENTLY HANDLE MISSING COST COLUMN)
# ==========================================
@st.cache_data
def load_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        # 1. Clean column names by stripping whitespace
        original_cols = df.columns.tolist()
        df.columns = df.columns.str.strip()
        
        # 2. Find and standardize the cost column name (case-insensitive)
        cost_col_match = [col for col in original_cols if col.strip().lower() == COST_COLUMN]
        
        if cost_col_match:
            # Rename the found cost column to a standardized internal name
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            # If the cost column isn't found, we silently create the standardized column with missing values (pd.NA).
            df[COST_COLUMN_FOUND] = pd.NA
            
        return df
    except Exception as e:
        st.error(f"❌ Error loading {file_path}. Please ensure the file exists and is readable: {e}")
        return pd.DataFrame()

# ==========================================
# READ BOTH FILES
# ==========================================
# Load the dataframes.
stock_df = load_excel(files["warehouse_stock"]["path"])
arrival_df = load_excel(files["new_arrival"]["path"])

# ==========================================
# DATA STRUCTURE (for internal use)
# ==========================================
data = {
    "stock": {
        "data": stock_df,
        "date": files["warehouse_stock"]["date"]
    },
    "new_arrival": {
        "data": arrival_df,
        "date": files["new_arrival"]["date"]
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
        filtered_stock_df = stock_df[stock_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category]
        filtered_arrival_df = arrival_df[arrival_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category]
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
    # THE SUCCESS MESSAGE IS REMOVED HERE
    
    # 1. Search warehouse stock (using original, unfiltered DF)
    results_stock = stock_df[
        stock_df.apply(lambda row: query in str(row.get("itembarcode", "")).lower() or
                                 query in str(row.get("description", "")).lower(), axis=1)
    ] if not stock_df.empty else pd.DataFrame()

    # 2. Search new arrivals (using original, unfiltered DF)
    results_arrival = arrival_df[
        arrival_df.apply(lambda row: query in str(row.get("itembarcode", "")).lower() or
                                     query in str(row.get("description", "")).lower(), axis=1)
    ] if not arrival_df.empty else pd.DataFrame()

    if not results_stock.empty or not results_arrival.empty:
        
        # Display Stock results: show_cost_in_table=True
        if not results_stock.empty:
            st.markdown("### 🏬 Found in Warehouse Stock")
            # Cost is visible in search (show_cost_in_table=True)
            st.dataframe(create_overview_df(results_stock, show_cost_in_table=True), use_container_width=True)
        
        # Display Arrival results: show_cost_in_table=True
        if not results_arrival.empty:
            st.markdown("### 🆕 Found in New Arrivals")
            # Cost is visible in search (show_cost_in_table=True)
            st.dataframe(create_overview_df(results_arrival, show_cost_in_table=True), use_container_width=True)
    else:
        st.warning(f"❌ No matching items found for **'{query}'** in either dataset.")
        
# ==========================================
# TABBED PAGE VIEWS (If no search query is active) (COST IS HIDDEN HERE)
# ==========================================
else:
    # Determine the status text based on category selection
    filter_status = f"({f'Filtered by **{selected_category}**' if selected_category != 'All Categories' else 'All Stock'})"

    tab1, tab2 = st.tabs(["🏬 Warehouse Stock", "🆕 New Arrival"])

    # Explicit warning that cost is hidden in the main view
    st.warning(f"⚠️ **{COST_COLUMN.upper()}** column is hidden in the standard tab view. Use the search bar to reveal cost for specific items.")
    
    with tab1:
        st.subheader("🏬 Warehouse Stock")
        st.write(f"📅 Last Updated: **{data['stock']['date']}** {filter_status}")

        if not filtered_stock_df.empty:
            # Display filtered stock: show_cost_in_table=False (COST IS HIDDEN)
            stock_overview_df = create_overview_df(filtered_stock_df, show_cost_in_table=False)
            st.dataframe(stock_overview_df, use_container_width=True)
            
        elif not stock_df.empty:
            st.info(f"No items found in Warehouse Stock for category: **{selected_category}**.")
        else:
            st.warning(f"⚠️ Could not display data from **{files['warehouse_stock']['path']}**.")

    with tab2:
        st.subheader("🆕 New Arrival")
        st.write(f"📅 Last Updated: **{data['new_arrival']['date']}** {filter_status}")

        if not filtered_arrival_df.empty:
            # Display filtered arrival: show_cost_in_table=False (COST IS HIDDEN)
            arrival_overview_df = create_overview_df(filtered_arrival_df, show_cost_in_table=False)
            st.dataframe(arrival_overview_df, use_container_width=True)
            
        elif not arrival_df.empty:
            st.info(f"No items found in New Arrivals for category: **{selected_category}**.")
        else:
            st.warning(f"⚠️ Could not display data from **{files['new_arrival']['path']}**.")
