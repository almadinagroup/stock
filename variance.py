import streamlit as st
import pandas as pd

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Stock & New Arrival Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# HIDE STREAMLIT UI (MENU / FORK / FOOTER)
# ==========================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="stDecoration"] {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEET CSV URLs
# ==========================================
URL_STOCK = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=0"
URL_NEW   = "https://docs.google.com/spreadsheets/d/1LStM9pRCR-MFW7XMXLPxjwJwjrhyspz0AP-_LtysyhY/export?format=csv&gid=419749881"

CATEGORY_COLUMN = "Category"
COST_COLUMN = "Cost"

# ==========================================
# LOAD DATA (KEEP COLUMN ORDER)
# ==========================================
@st.cache_data(ttl=600)
def load_sheet(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df.dropna(how="all")

stock_df = load_sheet(URL_STOCK)
new_df   = load_sheet(URL_NEW)

# ==========================================
# TITLE
# ==========================================
st.title("📦 Inventory Dashboard")
st.markdown("---")

# ==========================================
# CATEGORY FILTER (TOP OF PAGE)
# ==========================================
if CATEGORY_COLUMN in stock_df.columns and CATEGORY_COLUMN in new_df.columns:
    all_categories = pd.concat([
        stock_df[CATEGORY_COLUMN].astype(str),
        new_df[CATEGORY_COLUMN].astype(str)
    ]).str.strip().unique().tolist()

    all_categories.sort()
    all_categories.insert(0, "All Categories")

    selected_category = st.selectbox(
        "📂 Select Inventory Category",
        all_categories,
        index=0
    )

    if selected_category != "All Categories":
        filtered_stock_df = stock_df[
            stock_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category
        ]
        filtered_new_df = new_df[
            new_df[CATEGORY_COLUMN].astype(str).str.strip() == selected_category
        ]
    else:
        filtered_stock_df = stock_df
        filtered_new_df = new_df
else:
    filtered_stock_df = stock_df
    filtered_new_df = new_df

# ==========================================
# SEARCH BAR
# ==========================================
query = st.text_input(
    "🔍 Search Item Barcode or Description",
    placeholder="Enter barcode or item name..."
).strip().lower()

# ==========================================
# HELPERS
# ==========================================
def hide_columns(df, hide_cost=True):
    cols_to_drop = [CATEGORY_COLUMN]
    if hide_cost:
        cols_to_drop.append(COST_COLUMN)
    return df.drop(columns=cols_to_drop, errors="ignore")

def search_df(df, query):
    return df[df.apply(
        lambda row: query in str(row.get("itembarcode", "")).lower()
        or query in str(row.get("description", "")).lower(),
        axis=1
    )]

# ==========================================
# SEARCH RESULTS (COST SHOWN)
# ==========================================
if query:
    st.subheader(f"Search Results for: **{query}**")

    results_stock = search_df(stock_df, query)
    results_new   = search_df(new_df, query)

    if not results_stock.empty:
        st.markdown("### 🏬 Warehouse Stock")
        st.dataframe(
            hide_columns(results_stock, hide_cost=False),
            use_container_width=True
        )

    if not results_new.empty:
        st.markdown("### 🆕 New Arrivals")
        st.dataframe(
            hide_columns(results_new, hide_cost=False),
            use_container_width=True
        )

    if results_stock.empty and results_new.empty:
        st.warning("❌ No matching items found.")

# ==========================================
# NORMAL VIEW (COST HIDDEN)
# ==========================================
else:
    tab1, tab2 = st.tabs(["🏬 Warehouse Stock", "🆕 New Arrival"])

    with tab1:
        st.subheader("🏬 Warehouse Stock")
        st.dataframe(
            hide_columns(filtered_stock_df, hide_cost=True),
            use_container_width=True
        )

    with tab2:
        st.subheader("🆕 New Arrival")
        st.dataframe(
            hide_columns(filtered_new_df, hide_cost=True),
            use_container_width=True
        )
