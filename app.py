# ELECTRONIC SALES INTELLIGENCE
# Main Streamlit Dashboard Application

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from db1 import get_data, test_connection

# 1. Page Configuration

st.set_page_config(
    page_title="Electronics Sales Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 2. Load Existing CSS

def load_css():
    css_path = Path("assets/style.css")

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as file:
            st.markdown(
                f"<style>{file.read()}</style>",
                unsafe_allow_html=True
            )
    else:
        st.warning("File assets/style.css not found.")


load_css()


# 3. Database Connection

@st.cache_data(ttl=300)
def load_sales_data():

    query = """
        SELECT
            order_id,
            product,
            quantity_ordered,
            price_each,
            order_date,
            sales,
            city
        FROM staging.electronics_sales
    """

    df = get_data(query)

    df["order_date"] = pd.to_datetime(df["order_date"]) 
    df["sales"] = pd.to_numeric(df["sales"])
    df["quantity_ordered"] = pd.to_numeric(
        df["quantity_ordered"]
    )   

    return df


# 4. Sidebar Navigation

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <h2>ESI.</h2>
            <p>Electronics Sales Intelligence</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### Navigation")

    selected_page = st.radio(
        "Navigate",
        [
            "Overview",
            "Sales Report",
            "Product Insight",
            "City Insights"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("### Data Filter")

    date_filter = st.selectbox(
        "Period",
        [
            "All Data",
            "Today",
            "This Week",
            "This Month",
            "This Year"
        ],
        index=0
    )

    st.markdown("---")

    st.markdown("### City Filter")


# 5. Load Data

try:
    if not test_connection():
        st.error("Unable to connect to PostgreSQL.")
        st.stop()

    df = load_sales_data()

except Exception as error:

    st.error(f"Database error: {error}")
    st.stop()

if df.empty:
    st.warning("No Sales Data.")
    st.stop()


# 6. Filter Data

# The dataset is historical in nature.
# Today / Week / Month / Year are calculated based on 
# the most recent transaction in the dataset.

max_date = df["order_date"].max().normalize()

if date_filter == "Today":

    start_date = max_date
    end_date = max_date

elif date_filter == "This Week":

    start_date = max_date - pd.Timedelta(
        days=max_date.weekday()
    )
    end_date = max_date

elif date_filter == "This Year":

    start_date = max_date.replace(
        month=1,
        day=1
    )
    end_date = max_date

else:

    start_date = df["order_date"].min().normalize()
    end_date = max_date

df = df[
    (df["order_date"].dt.normalize() >= start_date)
    &
    (df["order_date"].dt.normalize() <= end_date)
].copy()

# City Filter

with st.sidebar:

    city_options = ["All Cities"] + sorted(
        df["city"].dropna().unique().tolist()
    )

    selected_city = st.selectbox(
        "Select City",
        city_options
    )

if selected_city != "All Cities":

    df = df[df["city"] == selected_city].copy()

if df.empty:
    st.warning("There are no transactions for the selectted filter.")
    st.stop()


# 7. Page Header

st.markdown(
    """
    <div class="page-header">
        <div>
            <h1>Electronics Sales Intelligence</h1>
            <p>Executive Overview & Sales Performance</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)



# 8. KPI Calculating

total_sales = df["sales"].sum()

total_orders = df["order_id"].nunique()

total_units = df["quantity_ordered"].sum()

total_products = df["product"].nunique()

average_order_value = (
    total_sales / total_orders
    if total_orders > 0 else 0
)


# 9. KPI Cards

st.markdown(
    """
    <div class="section-title">
        <h3>Business Overview</h3>
    </div>
    """,
    unsafe_allow_html=True
)

kpi_data = [
    ("💰", "Total Sales", f"${total_sales:,.0f}", "Total Revenue"),
    ("🛒", "Total Orders", f"{total_orders:,}", "Unique Orders"),
    ("📦", "Units Sold", f"{total_units:,.0f}", "Total Quantity"),
    ("📊", "Products", f"{total_products:,}", "Unique Products"),
    ("💵", "Average Order", f"${average_order_value:,.2f}", "Revenue per Order")
]

kpi_columns = st.columns(5, gap="small")

for col, (icon, label, value, caption) in zip(kpi_columns, kpi_data):
    with col:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-content">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-caption">{caption}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

st.markdown("---")

# 10. Geographical Sales Map

st.markdown(
    """
    <div class="section-title">
        <h3>Geographical Sales Distribution</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# CITY SALES DATA

city_sales = (
    df.groupby("city", as_index=False)
    .agg(
        total_sales=("sales", "sum"),
        total_units=("quantity_ordered", "sum"),
        total_orders=("order_id", "nunique")
    )
)

# City Coordinates for Map

city_coordinates = {
    "Atlanta": (33.7490, -84.3880),
    "Austin": (30.2672, -97.7431),
    "Boston": (42.3601, -71.0589),
    "Dallas": (32.7767, -96.7970),
    "Los Angeles": (34.0522, -118.2437),
    "New York City": (40.7128, -74.0060),
    "Portland": (45.5152, -122.6784),
    "San Francisco": (37.7749, -122.4194),
    "Seattle": (47.6062, -122.3321)
}

city_sales["latitude"] = city_sales["city"].map(
    lambda x: city_coordinates.get(x, (None, None))[0]
)

city_sales["longitude"] = city_sales["city"].map(
    lambda x: city_coordinates.get(x, (None, None))[1]
)

# Two-column layout
col_chart, pie_col = st.columns([1.5, 1], gap="medium")


# LEFT: SALES BY CITY

with col_chart:

    st.markdown(
        """
        <div class="section-title">
            <h3>Monthly Sales Trend</h3>
        </div>
        <p class="section-caption">
            Monthly revenue performance
        </p>
        """,
        unsafe_allow_html=True
    )

    monthly_trend = (
        df.assign(
            order_date=pd.to_datetime(df["order_date"])
        )
        .groupby(
            pd.Grouper(
                key="order_date",
                freq="MS"
            )
        )
        .agg(
            total_sales=("sales", "sum")
        )
        .reset_index()
    )

    fig_trend = px.line(
        monthly_trend,
        x="order_date",
        y="total_sales",
        markers=True,
        color_discrete_sequence=["#8061D9"]
    )

    fig_trend.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        fill="tozeroy",
        fillcolor="rgba(128,97,217,0.10)",
        hovertemplate=
        "%{x|%B %Y}<br>" +
        "Sales: $%{y:,.2f}<extra></extra>"
    )

    fig_trend.update_layout(
        height=390,
        margin=dict(l=10, r=20, t=15, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(
            family="Arial",
            color="#353B50"
        ),
        xaxis=dict(
            title=None,
            showgrid=False
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="#EAE3F7",
            tickprefix="$",
            tickformat="~s"
        )
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True,
        config={"displayModeBar":False}
    )


# RIGHT: SALES DISTRIBUTION PIE

with pie_col:

    st.markdown(
        """
        <div class="section-title">
            <h3>Sales Distribution</h3>
        </div>
        <p class="section-caption">
            Revenue contribution by product category
        </p>
        """,
        unsafe_allow_html=True
    )

    product_distribution = (
        df.groupby("product", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
    )

    top_5_distribution = product_distribution.head(5).copy()

    other_sales = (
        product_distribution.iloc[5:]["sales"].sum()
    )

    if other_sales > 0:

        top_5_distribution = pd.concat(
            [
                top_5_distribution,
                pd.DataFrame(
                    [{
                        "product": "Other Products",
                        "sales": other_sales
                    }]
                )
            ],
            ignore_index=True
        )

    fig_pie = px.pie(
        top_5_distribution,
        names="product",
        values="sales",
        hole=0.55,
        color_discrete_sequence=[
            "#5635A8",
            "#8061D9",
            "#A58CEB",
            "#C6B5F5",
            "#DED3FA",
            "#EEE8FF"
        ]
    )

    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(
            size=12,
            color="#FFFFFF"
        ),
        marker=dict(
            line=dict(
                color="#F3EDFF",
                width=3
            )
        ),
        hovertemplate=(
            "<b>%{label}</br><br>"
            "Sales: $%{value:,.2f}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        )
    )

    fig_pie.update_layout(
        height=400,

        # Light purple background
        paper_bgcolor="#F3EDFF",
        plot_bgcolor="#F3EDFF",

        # Pie chart position: centered and slightly upper
        xaxis=dict(
            domain=[0.12, 0.88]
        ),

        yaxis=dict(
            domain=[0.30, 1]
        ),

        # Legend below in 2 columns
        legend=dict(
            title_text="",
            orientation="h",
            x=0.5,
            y=0,
            xanchor="center",
            yanchor="top",
            entrywidth=0.35,
            entrywidthmode="fraction",
            font=dict(
                size=10,
                color="#49396C"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),

        margin=dict(l=15, r=15, t=15, b=10),

        font=dict(
            family="Arial",
            color="#352B50"
        )
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# 11. Top 10 Products

st.markdown("---")

left_col, right_col = st.columns(
    [1.5, 1],
    gap="large"
)

with left_col:

    st.markdown(

        """
        <div class="section-title">
            <h3>Top 10 Best Selling Product</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_products = (
        df.groupby("product", as_index=False)
        .agg(
            total_sales=("sales", "sum"),
            units_sold=("quantity_ordered", "sum")
        )
        .sort_values(
            "total_sales",
            ascending=False
        )
        .head(10)
        .sort_values("total_sales", ascending=True)
    )

    fig_products = px.bar(
        top_products,
        x="total_sales",
        y="product",
        orientation="h",
        text="total_sales",
        color="total_sales",
        color_continuous_scale=[
             "#E8DFFF",
             "#B9A4F5",
             "#8061D9",
             "#5635A8"
        ],
        hover_data={
            "units_sold":True,
            "total_sales": ":$,.2f"
        }
    )

    fig_products.update_traces(
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig_products.update_layout(
        height=430,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="total_sales ($)",
        yaxis_title="",
        margin=dict(l=10, r=50, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig_products,
        use_container_width=True
    )


# 12. Top 5 Cities

with right_col:

    st.markdown(
        """
        <div class="section-title">
            <h3>Top 5 Cities by Sales</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_cities = (
        city_sales
        .sort_values("total_sales", ascending=False)
        .head(5)
        .sort_values("total_sales", ascending=True)
    )

    fig_cities = px.bar(
        top_cities,
        x="total_sales",
        y="city",
        orientation="h",
        text="total_sales",
        color="total_sales",
        color_continuous_scale=[
            "#E8DFFF",
            "#B9A4F5",
            "#8061D9",
            "#5635A8"
        ]
    )

    fig_cities.update_traces(
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        cliponaxis=False
    )

    fig_cities.update_layout(
        height=430,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Total Sales ($)",
        yaxis_title="",
        margin=dict(l=10, r=50, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig_cities,
        use_container_width=True
    )
     

# 13. Sales Distribution - Pie Chart

st.markdown("---")

col_map, summart_col = st.columns(
    [1, 1.5],
    gap="large"
)


with col_map:

    st.markdown("### Sales Distribution Map")
    st.caption("Explore sales locations by city")


    map_data = city_sales.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    map_data = map_data[
        map_data["total_sales"] > 0
    ]

    if not map_data.empty:

        # Create map
        fig_map = px.scatter_map(
            map_data,
            lat="latitude",
            lon="longitude",
            size="total_sales",
            color="total_sales",
            hover_name="city",
            hover_data={
                "total_sales": ":$,.2f",
                "total_units": True,
                "total_orders": True,
                "latitude": False,
                "longitude": False
            },
            color_continuous_scale=[
                "#E8DFFF",
                "#B9A4F5",
                "#8061D9",
                "#5635A8"
            ],
            size_max=42,
            height=350,
            map_style="open-street-map"
        )

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#352B50")
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "scrollZoom": True
            }
        )

    else:
        st.info("No geographical data available.")

# 14. Sales Summary

with summart_col:

    st.markdown(
        """
        <div class="section-title">
            <h3>Sales Performance Summary</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    summary_data = (
        df.groupby("city", as_index=False)
        .agg(
            total_sales=("sales", "sum"),
            total_orders=("order_id", "nunique"),
            units_sold=("quantity_ordered", "sum")
        )
        .sort_values("total_sales", ascending=False)
    )

    summary_data["total_sales"] = (
        summary_data["total_sales"].map(
            lambda value: f"${value:,.2f}"
        )
    )

    st.dataframe(
        summary_data,
        use_container_width=True,
        hide_index=True,
        height=350
    )


# 15. Footer

st.markdown("---")

st.caption(
    "Electronics Sales Intelligence | "
    "Data Source: PostgreSQL | "
    "Built with Streamlit & Python"
)