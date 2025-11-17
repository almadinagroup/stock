import streamlit as st
import pandas as pd

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Stock & New Arrival Dashboard", layout="wide")

# ==========================================
# GOOGLE SHEET CSV URLs (Public)
# ==========================================
URL_STOCK = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=0"
URL_NEW   = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=419749881"

CATEGORY_COLUMN = "Category"
COST_COLUMN = "cost"
COST_COLUMN_FOUND = "internal_cost"

# ==========================================
# LOAD DATA FUNCTION
# ==========================================
@st.cache_data(ttl=600)
def load_sheet(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        cost_col_match = [c for c in df.columns if c.strip().lower() == COST_COLUMN]
        if cost_col_match:
            df = df.rename(columns={cost_col_match[0]: COST_COLUMN_FOUND})
        else:
            df[COST_COLUMN_FOUND] = pd.NA
        if CATEGORY_COLUMN not in df.columns:
            df[CATEGORY_COLUMN] = "Uncategorized"
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Error loading sheet from URL {url}: {e}")
        return pd.DataFrame()

# ==========================================
# LOAD BOTH SHEETS
# ==========================================
stock_df = load_sheet(URL_STOCK)
new_df   = load_sheet(URL_NEW)

# ==========================================
# HELPER FUNCTION FOR DISPLAY FORMATTING
# ==========================================
def create_overview_df(df, show_cost_in_table=False):
    if df.empty:
        return pd.DataFrame()
    
    df_display = df.copy()

    # Drop cost if not showing
    if not show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.drop(columns=[COST_COLUMN_FOUND])
    elif show_cost_in_table and COST_COLUMN_FOUND in df_display.columns:
        df_display = df_display.rename(columns={COST_COLUMN_FOUND: COST_COLUMN.upper()})
    
    # Drop Category column
    if CATEGORY_COLUMN in df_display.columns:
        df_display = df_display.drop(columns=[CATEGORY_COLUMN])
    
    return df_display

# ==========================================
# SIDEBAR FILTERING
# ==========================================
st.sidebar.title("Filter Options")

if CATEGORY_COLUMN in stock_df.columns and CATEGORY_COLUMN in new_df.columns:
    all_categories = pd.concat([
        stock_df[CATEGORY_COLUMN].dropna().astype(str),
        new_df[CATEGORY_COLUMN].dropna().astype(str)
    ]).str.strip().unique().tolist()
    all_categories.sort()
    all_categories.insert(0, "All Categories")

    selected_category = st.sidebar.selectbox("Select Inventory Category", all_categories, index=0)
    
    if selected_category != "All Categories":
        filtered_stock_df = stock_df[stock_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category.strip()]
        filtered_new_df = new_df[new_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category.strip()]
    else:
        filtered_stock_df = stock_df
        filtered_new_df = new_df
else:
    st.sidebar.warning(f"⚠️ Cannot find '{CATEGORY_COLUMN}' column. Displaying unfiltered data.")
    selected_category = "All Categories"
    filtered_stock_df = stock_df
    filtered_new_df = new_df

# ==========================================
# SEARCH BAR
# ==========================================
st.title("📦 Inventory Dashboard")
st.markdown("---")

query = st.text_input(
    "🔍 Search for Item Name or Barcode across all inventory:", 
    placeholder="Enter Barcode or Item Description here...",
    label_visibility="visible"
).strip().lower()

# ==========================================
# SEARCH LOGIC
# ==========================================
if query:
    st.subheader(f"Search Results for: **'{query}'**")
    
    def search_df(df, query):
        if df.empty:
            return pd.DataFrame()
        return df[df.apply(lambda row: query in str(row.get("itembarcode", "")).lower() or
                                     query in str(row.get("description", "")).lower(), axis=1)]

    results_stock = search_df(stock_df, query)
    results_new = search_df(new_df, query)

    if not results_stock.empty or not results_new.empty:
        
        if not results_stock.empty:
            st.markdown("### 🏬 Found in Warehouse Stock")
            st.dataframe(create_overview_df(results_stock, show_cost_in_table=True), use_container_width=True)
        
        if not results_new.empty:
            st.markdown("### 🆕 Found in New Arrivals")
            st.dataframe(create_overview_df(results_new, show_cost_in_table=True), use_container_width=True)
    else:
        st.warning(f"❌ No matching items found for **'{query}'** in either dataset.")

# ==========================================
# TABBED VIEWS
# ==========================================
else:
    filter_status = f"({f'Filtered by **{selected_category}**' if selected_category != 'All Categories' else 'All Stock'})"
    tab1, tab2 = st.tabs(["🏬 Warehouse Stock", "🆕 New Arrival"])
    
    with tab1:
        st.subheader("🏬 Warehouse Stock")
        st.write(f"📅 Last Updated: {pd.Timestamp.now().date()} {filter_status}")
        if not filtered_stock_df.empty:
            st.dataframe(create_overview_df(filtered_stock_df, show_cost_in_table=False), use_container_width=True)
        else:
            st.info(f"No items found in Warehouse Stock for category: **{selected_category}**.")

    with tab2:
        st.subheader("🆕 New Arrival")
        st.write(f"📅 Last Updated: {pd.Timestamp.now().date()} {filter_status}")
        if not filtered_new_df.empty:
            st.dataframe(create_overview_df(filtered_new_df, show_cost_in_table=False), use_container_width=True)
        else:
            st.info(f"No items found in New Arrivals for category: **{selected_category}**.")
